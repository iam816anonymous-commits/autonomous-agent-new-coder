from typing import Dict, Any
from repository.semantic.models import ConfidenceLevel
from .models import PlanningStatus, ChangePlan

class ConfidenceGatingEngine:
    """
    Evaluates ChangePlan confidence and evidence, returning READY, REQUIRES_DISCOVERY, REQUIRES_CLARIFICATION, BLOCKED, or HIGH_RISK.
    """
    @classmethod
    def evaluate_gating(cls, plan: ChangePlan) -> PlanningStatus:
        if not plan.discovery_result.get("sufficient_evidence", False):
            return PlanningStatus.REQUIRES_DISCOVERY

        if plan.confidence == ConfidenceLevel.HIGH and plan.request.risk_level in ("LOW", "MEDIUM"):
            return PlanningStatus.READY
        elif plan.confidence == ConfidenceLevel.MEDIUM:
            return PlanningStatus.REQUIRES_DISCOVERY
        elif plan.request.risk_level == "HIGH" or plan.request.risk_level == "CRITICAL":
            return PlanningStatus.HIGH_RISK
        elif plan.confidence in (ConfidenceLevel.LOW, ConfidenceLevel.UNKNOWN):
            return PlanningStatus.REQUIRES_CLARIFICATION

        return PlanningStatus.BLOCKED
