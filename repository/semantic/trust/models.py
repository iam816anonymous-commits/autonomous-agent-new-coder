from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from repository.semantic.models import Evidence, ConfidenceLevel

class SemanticTrustLevel(str, Enum):
    VERIFIED = "VERIFIED"
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    PARTIAL = "PARTIAL"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    UNKNOWN = "UNKNOWN"
    UNTRUSTED = "UNTRUSTED"

@dataclass
class SemanticTrustResult:
    symbol_id_or_name: str
    trust_level: SemanticTrustLevel
    confidence_score: float  # 0.0 to 1.0
    evidence: List[Evidence] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    allows_autonomous_modification: bool = False
