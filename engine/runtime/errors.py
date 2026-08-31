class RuntimeException(Exception):
    """Base exception for Mini-Jules verification runtime."""
    pass

class CommandRejectedError(RuntimeException):
    """Raised when an unregistered or disallowed command is attempted."""
    pass

class ExecutableNotAllowedError(CommandRejectedError):
    """Raised when an executable is not in the allowed policy list."""
    pass

class ArgumentNotAllowedError(CommandRejectedError):
    """Raised when command arguments violate allowed argument schemas or contain shell metacharacters."""
    pass

class WorkspaceBoundaryViolationError(RuntimeException):
    """Raised when execution or path resolution attempts to escape the repository workspace."""
    pass

class NetworkPolicyViolationError(RuntimeException):
    """Raised when a command requires network access prohibited by runtime policy."""
    pass

class ExecutionPolicyDeniedError(RuntimeException):
    """Raised when execution policy denies a command execution request."""
    pass

class PolicyViolationError(RuntimeException):
    """Raised when a command violates security or execution policies."""
    pass

class ExecutionTimeoutError(RuntimeException):
    """Raised when a command execution exceeds maximum allowed timeout."""
    pass

class WorkingDirectoryEscapeError(WorkspaceBoundaryViolationError):
    """Raised when a working directory escapes the repository root."""
    pass

class ExecutionApprovalRequiredError(RuntimeException):
    """Raised when high-risk execution (like running tests) lacks explicit execution_approved=True."""
    pass
