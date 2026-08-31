import os
import subprocess
import time
import uuid
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from .models import ExecutionResult, ExecutionStatus, CommandDefinition
from .policy import RuntimePolicy
from .errors import ExecutionTimeoutError

class ExecutionEnvironment(ABC):
    """
    Abstract interface for Mini-Jules command execution environments.
    Enables local restricted subprocess execution today and Docker sandbox execution in future phases.
    """
    @abstractmethod
    def execute_command(
        self,
        command_def: CommandDefinition,
        extra_arguments: List[str],
        working_directory: str,
        repo_root: str
    ) -> ExecutionResult:
        pass

class LocalRestrictedEnvironment(ExecutionEnvironment):
    """
    Local restricted subprocess execution environment.
    Strictly uses shell=False, enforces realpath boundaries, timeouts, output limits, and secret scrubbing.
    """
    def __init__(self, policy: Optional[RuntimePolicy] = None):
        self.policy = policy or RuntimePolicy()

    def execute_command(
        self,
        command_def: CommandDefinition,
        extra_arguments: List[str],
        working_directory: str,
        repo_root: str
    ) -> ExecutionResult:
        exec_id = f"EXEC-{uuid.uuid4().hex[:10]}"
        valid_cwd = self.policy.validate_working_directory(repo_root, working_directory)
        self.policy.validate_executable(command_def.executable)

        cmd_args = [command_def.executable] + command_def.base_arguments + extra_arguments
        env = self.policy.sanitize_environment()

        timeout = min(command_def.timeout_seconds, self.policy.max_timeout_seconds)
        started_at = time.time()

        try:
            proc = subprocess.Popen(
                cmd_args,
                cwd=valid_cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
                env=env
            )

            try:
                stdout_raw, stderr_raw = proc.communicate(timeout=timeout)
                finished_at = time.time()
                exit_code = proc.returncode
                status = ExecutionStatus.PASSED if exit_code == 0 else ExecutionStatus.FAILED
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout_raw, stderr_raw = proc.communicate()
                finished_at = time.time()
                exit_code = -1
                status = ExecutionStatus.TIMED_OUT

        except Exception as e:
            finished_at = time.time()
            return ExecutionResult(
                command_id=command_def.name,
                execution_id=exec_id,
                status=ExecutionStatus.CRASHED,
                exit_code=-1,
                started_at=started_at,
                finished_at=finished_at,
                duration=finished_at - started_at,
                stdout="",
                stderr=f"Runtime crash: {str(e)}",
                stdout_truncated=False,
                stderr_truncated=False
            )

        # Output truncation checks
        stdout_bytes = stdout_raw.encode("utf-8")
        stderr_bytes = stderr_raw.encode("utf-8")

        stdout_trunc = len(stdout_bytes) > self.policy.max_stdout_bytes
        stderr_trunc = len(stderr_bytes) > self.policy.max_stderr_bytes

        stdout = stdout_bytes[:self.policy.max_stdout_bytes].decode("utf-8", errors="ignore")
        stderr = stderr_bytes[:self.policy.max_stderr_bytes].decode("utf-8", errors="ignore")

        if stdout_trunc or stderr_trunc:
            if status == ExecutionStatus.PASSED:
                status = ExecutionStatus.OUTPUT_LIMIT_EXCEEDED

        return ExecutionResult(
            command_id=command_def.name,
            execution_id=exec_id,
            status=status,
            exit_code=exit_code,
            started_at=started_at,
            finished_at=finished_at,
            duration=finished_at - started_at,
            stdout=stdout,
            stderr=stderr,
            stdout_truncated=stdout_trunc,
            stderr_truncated=stderr_trunc
        )
