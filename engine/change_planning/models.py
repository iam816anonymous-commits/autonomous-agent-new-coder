from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import time
from repository.semantic.models import ConfidenceLevel, Evidence
from repository.semantic.trust.models import SemanticTrustLevel

class ChangeRequestType(str, Enum):
    FEATURE = "FEATURE"
    BUG_FIX = "BUG_FIX"
    REFACTOR = "REFACTOR"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    DEPENDENCY_CHANGE = "DEPENDENCY_CHANGE"
    ARCHITECTURAL_CHANGE = "ARCHITECTURAL_CHANGE"
    UNKNOWN = "UNKNOWN"

class OperationType(str, Enum):
    CREATE = "CREATE"
    MODIFY = "MODIFY"
    DELETE = "DELETE"
    MOVE = "MOVE"
    RENAME = "RENAME"
    CONFIGURE = "CONFIGURE"
    TEST = "TEST"
    VERIFY = "VERIFY"
    UNKNOWN = "UNKNOWN"

class PlanningStatus(str, Enum):
    READY = "READY"
    REQUIRES_DISCOVERY = "REQUIRES_DISCOVERY"
    REQUIRES_CLARIFICATION = "REQUIRES_CLARIFICATION"
    BLOCKED = "BLOCKED"
    HIGH_RISK = "HIGH_RISK"

@dataclass
class ChangeRequest:
    request_id: str
    user_intent: str
    request_type: ChangeRequestType
    description: str
    constraints: List[str] = field(default_factory=list)
    target_hints: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)
    risk_level: str = "LOW"

@dataclass
class ChangeStep:
    step_id: str
    description: str
    target_files: List[str] = field(default_factory=list)
    target_symbols: List[str] = field(default_factory=list)
    operation_type: OperationType = OperationType.MODIFY
    dependencies: List[str] = field(default_factory=list)
    preconditions: List[str] = field(default_factory=list)
    expected_outcomes: List[str] = field(default_factory=list)
    risk: str = "LOW"
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    evidence: List[Evidence] = field(default_factory=list)

@dataclass
class ChangePlan:
    plan_id: str
    request: ChangeRequest
    discovery_result: Dict[str, Any] = field(default_factory=dict)
    impact_analysis: Dict[str, Any] = field(default_factory=dict)
    steps: List[ChangeStep] = field(default_factory=list)
    assertions: List[Dict[str, Any]] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    trust_level: SemanticTrustLevel = SemanticTrustLevel.HIGH_CONFIDENCE
    status: PlanningStatus = PlanningStatus.READY
    created_at: float = field(default_factory=time.time)

@dataclass
class ExecutionResultContract:
    status: str
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    validation_results: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ChangeOutcome:
    plan_id: str
    expected_modified_files: List[str] = field(default_factory=list)
    actual_modified_files: List[str] = field(default_factory=list)
    unexpected_modified_files: List[str] = field(default_factory=list)
    expected_symbols: List[str] = field(default_factory=list)
    actual_symbols: List[str] = field(default_factory=list)
    unexpected_symbols: List[str] = field(default_factory=list)
    architectural_violations: List[str] = field(default_factory=list)
    match_status: str = "MATCH" # MATCH, UNEXPECTED_CHANGE, VIOLATION
