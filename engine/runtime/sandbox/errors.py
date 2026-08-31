"""
Typed error hierarchy for Sandbox and Capability subsystems.
"""

class SandboxError(Exception):
    """Base exception for all sandbox runtime errors."""
    pass

class CapabilityViolationError(SandboxError):
    """Raised when an operation attempts to exercise a capability that is denied or ungranted."""
    pass

class BackendUnavailableError(SandboxError):
    """Raised when a requested sandbox backend (e.g., Docker) is missing or unsupported."""
    pass

class WorkspaceEscapeError(SandboxError):
    """Raised when path traversal or symlinks attempt to access files outside the workspace boundary."""
    pass

class ApprovalExpiredError(SandboxError):
    """Raised when an execution approval has expired or does not match workspace fingerprint."""
    pass

class TransactionError(SandboxError):
    """Raised when a workspace transaction fails to initialize, commit, or rollback."""
    pass
