import time
from typing import Dict, Any, List, Optional
from .backend import SandboxBackend
from .models import SandboxSpec, SandboxResult, ExecutionCapability, SandboxStatus, SandboxMode
from .errors import CapabilityViolationError
from .capabilities import CapabilitySet
from .snapshot import WorkspaceSnapshotter

class StaticOnlyBackend(SandboxBackend):
    """
    Backend dedicated exclusively to static analysis (AST parsing, scanning, regex matching, hashing).
    Rejects any dynamic process execution, command invocation, or test running.
    """
    def __init__(self, spec: SandboxSpec):
        super().__init__(spec)
        if spec.mode != SandboxMode.STATIC_ONLY:
            raise CapabilityViolationError(f"StaticOnlyBackend requires STATIC_ONLY mode, got {spec.mode.value}")

        # Capability set check
        self.capability_set = CapabilitySet(spec.allowed_capabilities)
        # Disallow dynamic execution capabilities
        for forbidden in (ExecutionCapability.EXECUTE_COMMAND, ExecutionCapability.RUN_TESTS, ExecutionCapability.INSTALL_DEPENDENCY, ExecutionCapability.NETWORK):
            if self.capability_set.has(forbidden):
                raise CapabilityViolationError(f"StaticOnlyBackend cannot grant dynamic capability: '{forbidden.value}'")

    def create(self) -> None:
        self.status = SandboxStatus.READY

    def prepare(self) -> None:
        pass

    def execute(self, command_name: str, args: List[str], env: Optional[Dict[str, str]] = None) -> SandboxResult:
        """
        Always rejects dynamic execution attempts in STATIC_ONLY mode.
        """
        start_time = time.time()
        self.status = SandboxStatus.FAILED
        duration = time.time() - start_time

        violation_msg = f"STATIC_ONLY mode rejects process/command execution attempt for '{command_name}'."

        return SandboxResult(
            sandbox_id=self.spec.sandbox_id,
            status=SandboxStatus.FAILED,
            execution_result={
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": violation_msg,
                "error": violation_msg
            },
            enforcement_metadata=self.enforcement_status(),
            warnings=["Static analysis backend invoked with execution command."],
            violations=[violation_msg],
            duration=duration,
            cleanup_result={"cleaned": True}
        )

    def terminate(self) -> None:
        self.status = SandboxStatus.TERMINATED

    def cleanup(self) -> Dict[str, Any]:
        return {"cleaned": True}

    def supports_capability(self, capability: ExecutionCapability) -> bool:
        allowed_static = {ExecutionCapability.STATIC_ANALYSIS, ExecutionCapability.READ_WORKSPACE}
        return capability in allowed_static and self.capability_set.has(capability)

    def enforcement_status(self) -> Dict[str, Any]:
        return {
            "mode": SandboxMode.STATIC_ONLY.value,
            "os_process_isolation": True,
            "code_execution_blocked": True,
            "network_isolation": "ENFORCED_STATIC_DENY",
            "enforceable_limits": self.spec.resource_limits.enforceable_limits,
            "limitations": []
        }
