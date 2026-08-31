"""
Typed exception hierarchy for Phase F Orchestrator.
"""

class OrchestrationError(Exception):
    """Base exception for all orchestration errors."""
    pass

class PlanningError(OrchestrationError):
    """Raised when deterministic plan generation fails."""
    pass

class PlanValidationError(OrchestrationError):
    """Raised when an engineering plan fails structural or boundary validation."""
    pass

class OperatorAmbiguityError(OrchestrationError):
    """Raised when multiple operators match a task without priority ordering."""
    pass

class ApprovalRequiredError(OrchestrationError):
    """Raised when execution or application occurs without required explicit approval."""
    pass

class RecoveryError(OrchestrationError):
    """Raised when process crash recovery or bounded replanning fails."""
    pass
