class OperatorError(Exception):
    """Base exception for engineering operator failures."""
    pass

class PreconditionFailedError(OperatorError):
    """Raised when an operator precondition is unsatisfied."""
    pass

class StaleProposalError(OperatorError):
    """Raised when a proposal's SHA256 content hash no longer matches current workspace state."""
    pass

class ApprovalRequiredError(OperatorError):
    """Raised when an apply operation is attempted with approved=False."""
    pass

class RollbackError(OperatorError):
    """Raised when an operator transaction rollback fails."""
    pass
