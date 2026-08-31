from typing import Dict, Any
from .models import ConfidenceLevel

class ConfidenceModel:
    """
    Assigns explicit confidence levels based on extraction mechanisms.
    HIGH: AST definition, exact import resolution.
    MEDIUM: Cross-module name match, structural conventions.
    LOW: Heuristic name matching.
    UNKNOWN: Dynamic dispatch, reflection, unresolved import.
    """
    @classmethod
    def evaluate_confidence(cls, mechanism: str, resolved_uniquely: bool) -> ConfidenceLevel:
        if mechanism == "AST" and resolved_uniquely:
            return ConfidenceLevel.HIGH
        elif mechanism == "AST":
            return ConfidenceLevel.MEDIUM
        elif mechanism == "HEURISTIC" and resolved_uniquely:
            return ConfidenceLevel.MEDIUM
        elif mechanism == "HEURISTIC":
            return ConfidenceLevel.LOW
        return ConfidenceLevel.UNKNOWN
