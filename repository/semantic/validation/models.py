from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

class ValidationStatus(str, Enum):
    VALID = "VALID"
    PARTIALLY_VALID = "PARTIALLY_VALID"
    INVALID = "INVALID"
    INCONCLUSIVE = "INCONCLUSIVE"

class IssueSeverity(str, Enum):
    BLOCKING = "BLOCKING"
    WARNING = "WARNING"
    INFO = "INFO"

@dataclass
class ValidationIssue:
    issue_type: str
    description: str
    severity: IssueSeverity
    affected_symbol_id: Optional[str] = None
    affected_file: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationResult:
    status: ValidationStatus
    issues: List[ValidationIssue] = field(default_factory=list)
    dangling_node_count: int = 0
    unresolved_reference_count: int = 0
    duplicate_symbol_count: int = 0
