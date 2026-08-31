class RuntimeException(Exception):
    """Base exception for Mini-Jules verification runtime."""
    pass

class CommandRejectedError(RuntimeException):
    """Raised when an unregistered or disallowed command is attempted."""
    pass

class PolicyViolationError(RuntimeException):
    """Raised when a command violates security or execution policies."""
    pass

class ExecutionTimeoutError(RuntimeException):
    """Raised when a command execution exceeds maximum allowed timeout."""
    pass

class WorkingDirectoryEscapeError(RuntimeException):
    """Raised when a working directory escapes the repository root."""
    pass

class ExecutionApprovalRequiredError(RuntimeException):
    """Raised when high-risk execution (like running tests) lacks explicit execution_approved=True."""
    pass
