import time
import os
from typing import Dict, Any, List, Optional
from .backend import SandboxBackend
from .models import SandboxSpec, SandboxResult, ExecutionCapability, SandboxStatus, SandboxMode, ExecutionTrustLevel
from .errors import CapabilityViolationError
from .capabilities import CapabilitySet
from ..executor import CommandExecutor
from ..models import CommandRequest, ExecutionRiskLevel
from ..policy import RuntimePolicy

class RestrictedLocalBackend(SandboxBackend):
    """
    Backend executing authorized commands in local restricted environment.
    Enforces argument schema validation, shell=False, realpath boundary, environment secret blocking,
    and explicitly discloses local isolation limitations (e.g., lack of OS kernel network namespace isolation).
    """
    def __init__(self, spec: SandboxSpec):
        super().__init__(spec)
        self.capability_set = CapabilitySet(spec.allowed_capabilities)
        self.executor = CommandExecutor()

    def create(self) -> None:
        self.status = SandboxStatus.READY

    def prepare(self) -> None:
        pass

    def execute(self, command_name: str, args: List[str], env: Optional[Dict[str, str]] = None) -> SandboxResult:
        start_time = time.time()
        self.status = SandboxStatus.RUNNING

        # 1. Check capability
        if not self.capability_set.has(ExecutionCapability.EXECUTE_COMMAND) and not self.capability_set.has(ExecutionCapability.RUN_TESTS):
            self.status = SandboxStatus.FAILED
            msg = f"RestrictedLocalBackend rejected execution: missing EXECUTE_COMMAND or RUN_TESTS capability."
            return SandboxResult(
                sandbox_id=self.spec.sandbox_id,
                status=SandboxStatus.FAILED,
                execution_result={"success": False, "exit_code": -1, "stdout": "", "stderr": msg, "error": msg},
                enforcement_metadata=self.enforcement_status(),
                violations=[msg],
                duration=time.time() - start_time
            )

        # 2. Prepare request
        req = CommandRequest(
            command_name=command_name,
            extra_arguments=args,
            working_directory="."
        )

        # 3. Execute via CommandExecutor
        exec_approved = self.spec.trust_level in (ExecutionTrustLevel.TRUSTED_TOOL_ONLY, ExecutionTrustLevel.UNTRUSTED_REPOSITORY_CODE)
        try:
            exec_res = self.executor.execute(
                request=req,
                repo_root=self.spec.workspace_root,
                task_id=self.spec.sandbox_id,
                execution_approved=exec_approved
            )
            duration = time.time() - start_time
            success = exec_res.status.value == "PASSED"
            final_status = SandboxStatus.COMPLETED if success else SandboxStatus.FAILED
            self.status = final_status

            warnings = []
            if self.spec.network_access.value == "DENY":
                warnings.append("Local process execution cannot guarantee kernel-level network socket blocking.")

            return SandboxResult(
                sandbox_id=self.spec.sandbox_id,
                status=final_status,
                execution_result={
                    "command_name": command_name,
                    "success": success,
                    "exit_code": exec_res.exit_code,
                    "stdout": exec_res.stdout,
                    "stderr": exec_res.stderr,
                    "duration": duration,
                    "timed_out": exec_res.status.value == "TIMED_OUT"
                },
                enforcement_metadata=self.enforcement_status(),
                warnings=warnings,
                violations=[],
                duration=duration,
                cleanup_result={"cleaned": True}
            )
        except Exception as e:
            duration = time.time() - start_time
            self.status = SandboxStatus.FAILED
            return SandboxResult(
                sandbox_id=self.spec.sandbox_id,
                status=SandboxStatus.FAILED,
                execution_result={
                    "command_name": command_name,
                    "success": False,
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": str(e),
                    "duration": duration,
                    "error": str(e)
                },
                enforcement_metadata=self.enforcement_status(),
                warnings=[],
                violations=[str(e)],
                duration=duration,
                cleanup_result={"cleaned": True}
            )

    def terminate(self) -> None:
        self.status = SandboxStatus.TERMINATED

    def cleanup(self) -> Dict[str, Any]:
        return {"cleaned": True}

    def supports_capability(self, capability: ExecutionCapability) -> bool:
        supported = {
            ExecutionCapability.STATIC_ANALYSIS,
            ExecutionCapability.READ_WORKSPACE,
            ExecutionCapability.WRITE_WORKSPACE,
            ExecutionCapability.EXECUTE_COMMAND,
            ExecutionCapability.RUN_TESTS
        }
        return capability in supported and self.capability_set.has(capability)

    def enforcement_status(self) -> Dict[str, Any]:
        return {
            "mode": SandboxMode.RESTRICTED_LOCAL.value,
            "shell_execution_blocked": True,
            "realpath_boundary_enforced": True,
            "environment_secrets_sanitized": True,
            "network_isolation": "BEST_EFFORT_LOCAL_NO_KERNEL_NS",
            "enforceable_limits": ["timeout_seconds", "max_output_bytes"],
            "limitations": [
                "Local execution relies on host OS permissions.",
                "Kernel-level network namespace isolation is not available without containerization.",
                "Resource limits (RAM/CPU) are constrained to timeout and output size enforcement."
            ]
        }
