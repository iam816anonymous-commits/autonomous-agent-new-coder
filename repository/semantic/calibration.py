from typing import Dict, Any, List
from repository.semantic.models import ConfidenceLevel

class ConfidenceCalibrator:
    """
    Computes deterministic confidence scores based on AST evidence, unique resolutions, ambiguity factors, and dynamic constructs.
    """
    @classmethod
    def calculate_confidence(
        cls,
        mechanism: str,
        is_unique: bool,
        has_dynamic_features: bool = False,
        is_star_import: bool = False
    ) -> Dict[str, Any]:
        score = 1.0
        factors = []

        if mechanism == "AST":
            factors.append("DIRECT_AST_EVIDENCE")
        else:
            score -= 0.3
            factors.append("HEURISTIC_EXTRACTION")

        if is_unique:
            factors.append("UNIQUE_SYMBOL_MATCH")
        else:
            score -= 0.3
            factors.append("MULTIPLE_CANDIDATES")

        if has_dynamic_features:
            score -= 0.4
            factors.append("DYNAMIC_ATTRIBUTE_ACCESS")

        if is_star_import:
            score -= 0.3
            factors.append("STAR_IMPORT")

        score = max(0.0, min(1.0, score))

        if score >= 0.85:
            level = ConfidenceLevel.HIGH
        elif score >= 0.50:
            level = ConfidenceLevel.MEDIUM
        elif score >= 0.20:
            level = ConfidenceLevel.LOW
        else:
            level = ConfidenceLevel.UNKNOWN

        return {
            "score": score,
            "confidence_level": level.value,
            "contributing_factors": factors
        }
