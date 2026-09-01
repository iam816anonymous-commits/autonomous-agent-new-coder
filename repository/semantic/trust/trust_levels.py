from typing import List, Optional
from .models import SemanticTrustLevel, SemanticTrustResult
from repository.semantic.models import SemanticSymbol, Evidence, ConfidenceLevel

class SemanticTrustEvaluator:
    """
    Evaluates semantic symbols and query results to assign explicit trust levels and autonomy permissions.
    """
    @classmethod
    def evaluate_symbol_trust(cls, symbol: SemanticSymbol, evidence_list: Optional[List[Evidence]] = None) -> SemanticTrustResult:
        ev = evidence_list or []
        assumptions = []
        limitations = []

        if symbol.confidence == ConfidenceLevel.HIGH:
            trust = SemanticTrustLevel.HIGH_CONFIDENCE
            score = 0.95
            allows_auto = True
        elif symbol.confidence == ConfidenceLevel.MEDIUM:
            trust = SemanticTrustLevel.PARTIAL
            score = 0.70
            allows_auto = False
            assumptions.append("Symbol resolved via cross-module naming match or structural convention.")
        elif symbol.confidence == ConfidenceLevel.LOW:
            trust = SemanticTrustLevel.LOW_CONFIDENCE
            score = 0.40
            allows_auto = False
            limitations.append("Symbol match relies on heuristic name lookup.")
        else:
            trust = SemanticTrustLevel.UNKNOWN
            score = 0.0
            allows_auto = False
            limitations.append("Symbol resolution is unresolved or dynamic.")

        return SemanticTrustResult(
            symbol_id_or_name=symbol.symbol_id,
            trust_level=trust,
            confidence_score=score,
            evidence=ev,
            assumptions=assumptions,
            limitations=limitations,
            allows_autonomous_modification=allows_auto
        )
