"""
Typed exceptions for semantic trust model and safety boundaries.
"""

class TrustError(Exception):
    """Base exception for semantic trust errors."""
    pass

class UntrustedSymbolError(TrustError):
    """Raised when an operation targets an untrusted or unknown symbol."""
    pass

class TrustBoundaryViolationError(TrustError):
    """Raised when an autonomous modification is attempted without required trust level."""
    pass
