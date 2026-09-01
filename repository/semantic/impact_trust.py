from typing import Dict, Any
from repository.semantic.models import SemanticImpactReport, ConfidenceLevel

class SemanticImpactTrustGate:
    """
    Evaluates semantic impact reports and enforces trust gate decisions:
    HIGH_TRUST_IMPACT, PARTIAL_IMPACT, or INCONCLUSIVE_IMPACT.
    """
    @classmethod
    def evaluate_impact_trust(cls, report: SemanticImpactReport) -> Dict[str, Any]:
        if report.confidence == ConfidenceLevel.HIGH and report.blast_radius in ("LOW", "MEDIUM"):
            trust = "HIGH_TRUST_IMPACT"
            allows_auto = True
        elif report.confidence in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM):
            trust = "PARTIAL_IMPACT"
            allows_auto = False
        else:
            trust = "INCONCLUSIVE_IMPACT"
            allows_auto = False

        return {
            "impact_trust_level": trust,
            "target_symbol": report.target_symbol,
            "blast_radius": report.blast_radius,
            "allows_autonomous_execution": allows_auto,
            "affected_files": report.affected_files
        }
