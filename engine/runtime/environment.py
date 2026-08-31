import os
import subprocess
import time
import uuid
import hashlib
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from .models import ExecutionResult, ExecutionStatus, CommandDefinition
from .policy import RuntimePolicy
from .errors import ExecutionTimeoutError

IGNORE_HASH_DIRS = {
    ".git", "venv", ".venv", "artifacts", "node_modules",
    "__pycache__", ".pytest_cache", "dist", "build"
}

def compute_workspace_snapshot_hash(repo_root: str) -> str:
    """
    Computes a deterministic lightweight workspace identity hash.
    Skips ignored directories (.git, venv, artifacts, node_modules, __pycache__).
    """
    hasher = hashlib.sha256()
    real_root = os.path.realpath(os.path.abspath(repo_root))

    for current_root, dirs, files in os.walk(real_root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in IGNORE_HASH_DIRS and not d.startswith(".")]

        for filename in sorted(files):
            full_path = os.path.join(current_root, filename)
            rel_path = os.path.relpath(full_path, real_root).replace("\\", "/")

            hasher.update(rel_path.encode("utf-8"))

            # Hash file content if under 5MB
            try:
                if os.path.getsize(full_path) < 5 * 1024 * 1024:
                    with open(full_path, "rb") as f:
                        hasher.update(f.read())
            except Exception:
                pass

    return hasher.hexdigest()

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
    Strictly uses shell=False, enforces realpath boundaries, timeouts, output limits, secret scrubbing,
    and workspace change detection.
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
        snapshot_before = compute_workspace_snapshot_hash(repo_root)
        started_at = time.time()

        try:
            proc = subprocess.Popen(
                cmd_args,
                cwd=valid_cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,  # Binary capture for safe decoding
                shell=False,
                env=env
            )

            try:
                stdout_bytes, stderr_bytes = proc.communicate(timeout=timeout)
                finished_at = time.time()
                exit_code = proc.returncode
                status = ExecutionStatus.PASSED if exit_code == 0 else ExecutionStatus.FAILED
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout_bytes, stderr_bytes = proc.communicate()
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
                stderr=self.policy.redact_text(f"Runtime crash: {str(e)}"),
                resolved_executable=command_def.executable,
                arguments=cmd_args,
                working_directory=working_directory,
                workspace_snapshot_hash=snapshot_before
            )

        snapshot_after = compute_workspace_snapshot_hash(repo_root)
        if snapshot_before != snapshot_after:
            status = ExecutionStatus.WORKSPACE_CHANGED

        # Output truncation & secret redaction
        stdout_trunc = len(stdout_bytes) > self.policy.max_stdout_bytes
        stderr_trunc = len(stderr_bytes) > self.policy.max_stderr_bytes

        stdout_raw = stdout_bytes[:self.policy.max_stdout_bytes].decode("utf-8", errors="replace")
        stderr_raw = stderr_bytes[:self.policy.max_stderr_bytes].decode("utf-8", errors="replace")

        stdout = self.policy.redact_text(stdout_raw)
        stderr = self.policy.redact_text(stderr_raw)

        if (stdout_trunc or stderr_trunc) and status == ExecutionStatus.PASSED:
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
            resolved_executable=command_def.executable,
            arguments=cmd_args,
            working_directory=working_directory,
            policy_decision="PERMITTED",
            workspace_snapshot_hash=snapshot_after,
            environment_mode="LOCAL_RESTRICTED",
            stdout_truncated=stdout_trunc,
            stderr_truncated=stderr_trunc
        )
