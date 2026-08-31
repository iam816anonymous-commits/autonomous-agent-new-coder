"""
Typed exceptions for workflow durability, checkpointing, and replay.
"""

class DurabilityError(Exception):
    """Base exception for all durability subsystem errors."""
    pass

class CheckpointError(DurabilityError):
    """Raised when checkpoint creation, retrieval, or sequence integrity fails."""
    pass

class IdempotencyViolationError(DurabilityError):
    """Raised when a side-effecting step is re-executed with conflicting state."""
    pass

class RecoveryError(DurabilityError):
    """Raised when crash recovery or resume safety checks fail."""
    pass

class ReplayError(DurabilityError):
    """Raised when deterministic workflow replay fails fingerprint or state checks."""
    pass
