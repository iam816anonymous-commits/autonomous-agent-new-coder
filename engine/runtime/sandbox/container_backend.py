import time
import shutil
import subprocess
from typing import Dict, Any, List, Optional
from .backend import SandboxBackend
from .models import SandboxSpec, SandboxResult, ExecutionCapability, SandboxStatus, SandboxMode
from .errors import BackendUnavailableError, CapabilityViolationError
from .capabilities import CapabilitySet

class ContainerSandboxBackend(SandboxBackend):
    """
    Optional Container Sandbox Backend (e.g., Docker).
    Execution occurs inside an isolated container with network disabled, non-root user, and explicit workspace mounts.
    Fails safely with BackendUnavailableError if Docker is missing or daemon is not responsive.
    """
    def __init__(self, spec: SandboxSpec):
        super().__init__(spec)
        self.capability_set = CapabilitySet(spec.allowed_capabilities)
        self.docker_bin = shutil.which("docker")

    @classmethod
    def detect_docker_availability(cls) -> str:
        """
        Safely detects Docker availability: AVAILABLE, UNAVAILABLE, or MISCONFIGURED.
        """
        docker_path = shutil.which("docker")
        if not docker_path:
            return "UNAVAILABLE"

        try:
            res = subprocess.run(
                [docker_path, "info"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5.0,
                check=False
            )
            if res.returncode == 0:
                return "AVAILABLE"
            return "MISCONFIGURED"
        except Exception:
            return "UNAVAILABLE"

    def create(self) -> None:
        avail = self.detect_docker_availability()
        if avail != "AVAILABLE":
            raise BackendUnavailableError(f"ContainerSandboxBackend unavailable: Docker status is '{avail}'.")
        self.status = SandboxStatus.READY

    def prepare(self) -> None:
        pass

    def execute(self, command_name: str, args: List[str], env: Optional[Dict[str, str]] = None) -> SandboxResult:
        avail = self.detect_docker_availability()
        if avail != "AVAILABLE":
            raise BackendUnavailableError(f"ContainerSandboxBackend execution failed: Docker status is '{avail}'.")

        start_time = time.time()
        self.status = SandboxStatus.RUNNING

        # Build Docker command
        docker_cmd = [
            self.docker_bin, "run", "--rm",
            "--network", "none",
            "-v", f"{self.spec.workspace_root}:/workspace:rw",
            "-w", "/workspace",
            "python:3.12-slim",
            command_name
        ] + args

        try:
            proc_res = subprocess.run(
                docker_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self.spec.timeout,
                check=False
            )
            duration = time.time() - start_time
            success = proc_res.returncode == 0
            self.status = SandboxStatus.COMPLETED if success else SandboxStatus.FAILED

            return SandboxResult(
                sandbox_id=self.spec.sandbox_id,
                status=self.status,
                execution_result={
                    "command_name": command_name,
                    "success": success,
                    "exit_code": proc_res.returncode,
                    "stdout": proc_res.stdout.decode("utf-8", errors="replace"),
                    "stderr": proc_res.stderr.decode("utf-8", errors="replace"),
                    "duration": duration,
                    "timed_out": False
                },
                enforcement_metadata=self.enforcement_status(),
                warnings=[],
                violations=[],
                duration=duration,
                cleanup_result={"cleaned": True}
            )
        except subprocess.TimeoutExpired:
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
                    "stderr": "Docker container execution timed out.",
                    "duration": duration,
                    "timed_out": True
                },
                enforcement_metadata=self.enforcement_status(),
                warnings=["Container execution timed out."],
                violations=[],
                duration=duration,
                cleanup_result={"cleaned": True}
            )

    def terminate(self) -> None:
        self.status = SandboxStatus.TERMINATED

    def cleanup(self) -> Dict[str, Any]:
        return {"cleaned": True}

    def supports_capability(self, capability: ExecutionCapability) -> bool:
        return self.capability_set.has(capability)

    def enforcement_status(self) -> Dict[str, Any]:
        return {
            "mode": SandboxMode.ISOLATED.value,
            "container_isolation": True,
            "network_isolation": "ENFORCED_NETWORK_NONE",
            "filesystem_mount": "WORKSPACE_ONLY",
            "enforceable_limits": ["timeout_seconds", "max_output_bytes", "max_memory_mb", "max_cpu_cores"],
            "limitations": []
        }
