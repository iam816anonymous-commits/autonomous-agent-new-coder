import os
import re
from typing import Set, Dict, List, Optional
from .models import ExecutionRiskLevel, ExecutionCapability
from .errors import PolicyViolationError, WorkingDirectoryEscapeError, NetworkPolicyViolationError

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
        require_approval_for_high_risk: bool = True,
        allow_network_access: bool = False,
        redact_configured_secrets: bool = True
    ):
        self.max_timeout_seconds = max_timeout_seconds
        self.max_stdout_bytes = max_stdout_bytes
        self.max_stderr_bytes = max_stderr_bytes
        self.require_approval_for_high_risk = require_approval_for_high_risk
        self.allow_network_access = allow_network_access
        self.redact_configured_secrets = redact_configured_secrets

    def validate_executable(self, executable: str):
        base_name = os.path.basename(executable).lower()
        if base_name in BLOCKED_EXECUTABLES:
            raise PolicyViolationError(
                f"Policy Rejection: Executable '{executable}' is strictly blocked from execution."
            )

    def validate_capabilities(self, capabilities: List[ExecutionCapability]):
        if ExecutionCapability.NETWORK_ACCESS in capabilities and not self.allow_network_access:
            raise NetworkPolicyViolationError(
                "Network Policy Rejection: Command explicitly requires NETWORK_ACCESS capability which is disabled by policy."
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

    def redact_text(self, text: str, parent_env: Optional[Dict[str, str]] = None) -> str:
        if not text or not self.redact_configured_secrets:
            return text

        redacted = text
        source = parent_env or os.environ

        # Collect secret values from parent process environment
        secret_values = []
        for k, v in source.items():
            if any(s in k.lower() for s in ["key", "secret", "token", "auth", "passwd"]):
                if len(v.strip()) > 3:
                    secret_values.append(v.strip())

        for secret in secret_values:
            redacted = redacted.replace(secret, "[REDACTED_SECRET]")

        # Regex patterns for common secret formats
        patterns = [
            r'sk-[a-zA-Z0-9]{20,}',
            r'AKIA[0-9A-Z]{16}',
            r'ghp_[a-zA-Z0-9]{36}',
            r'-----BEGIN [A-Z ]+ PRIVATE KEY-----'
        ]
        for p in patterns:
            redacted = re.sub(p, "[REDACTED_SECRET]", redacted)

        return redacted
