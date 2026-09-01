"""
Typed exception hierarchy for change planning.
"""

class ChangePlanningError(Exception):
    """Base exception for change planning errors."""
    pass

class DiscoveryError(ChangePlanningError):
    """Raised when repository change discovery fails or evidence is insufficient."""
    pass

class PreExecutionAssertionError(ChangePlanningError):
    """Raised when pre-execution assertions fail prior to change application."""
    pass
