import os
from typing import Set, Dict, List, Optional
from .models import ExecutionRiskLevel
from .errors import PolicyViolationError, WorkingDirectoryEscapeError

BLOCKED_EXECUTABLES: Set[str] = {
    "bash", "sh", "zsh", "cmd", "powershell", "pwsh",
    "curl", "wget", "ssh", "scp", "git", "pip", "apt", "apt-get",
    "rm", "dd", "mkfs", "sudo", "su", "eval", "exec"
}

ALLOWED_ENV_VARS: Set[str] = {
    "PATH", "PYTHONPATH", "HOME", "USER", "TMPDIR", "TEMP", "LANG", "LC_ALL"
}

class RuntimePolicy:
    """
    Security and execution policy enforcer for Mini-Jules verification runtime.
    Blocks shell interpreters, enforces boundary isolation, limits timeouts/output sizes, and scrubs secrets.
    """
    def __init__(
        self,
        max_timeout_seconds: float = 120.0,
        max_stdout_bytes: int = 100000,
        max_stderr_bytes: int = 100000,
        require_approval_for_high_risk: bool = True
    ):
        self.max_timeout_seconds = max_timeout_seconds
        self.max_stdout_bytes = max_stdout_bytes
        self.max_stderr_bytes = max_stderr_bytes
        self.require_approval_for_high_risk = require_approval_for_high_risk

    def validate_executable(self, executable: str):
        base_name = os.path.basename(executable).lower()
        if base_name in BLOCKED_EXECUTABLES:
            raise PolicyViolationError(
                f"Policy Rejection: Executable '{executable}' is strictly blocked from execution."
            )

    def validate_working_directory(self, repo_root: str, target_dir: str) -> str:
        real_root = os.path.realpath(os.path.abspath(repo_root))
        real_target = os.path.realpath(os.path.abspath(os.path.join(real_root, target_dir)))

        try:
            if os.path.commonpath([real_root, real_target]) != real_root:
                raise WorkingDirectoryEscapeError(
                    f"Policy Rejection: Working directory '{target_dir}' escapes repository root '{repo_root}'."
                )
        except ValueError:
            raise WorkingDirectoryEscapeError(
                f"Policy Rejection: Working directory '{target_dir}' escapes repository root '{repo_root}'."
            )

        return real_target

    def sanitize_environment(self, parent_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        source = parent_env or os.environ
        sanitized = {}

        for key in ALLOWED_ENV_VARS:
            if key in source:
                sanitized[key] = source[key]

        # Explicitly scrub parent process secrets
        secret_keys = [k for k in source.keys() if any(s in k.lower() for s in ["key", "secret", "token", "auth", "passwd"])]
        for k in secret_keys:
            sanitized.pop(k, None)

        return sanitized
