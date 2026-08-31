"""
Orchestration domain models for Phase F Deterministic Engineering Orchestrator.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
import time
from engine.classifier.models import TaskType, TaskClassification
from engine.runtime.sandbox.models import SandboxMode, ExecutionTrustLevel, ExecutionCapability, TransactionPolicy

class OrchestrationState(Enum):
    CREATED = "CREATED"
    ANALYZING_REPOSITORY = "ANALYZING_REPOSITORY"
    CLASSIFYING_TASK = "CLASSIFYING_TASK"
    PLANNING = "PLANNING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    DIAGNOSING_FAILURE = "DIAGNOSING_FAILURE"
    REPLANNING = "REPLANNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"

class PlanStepStatus(Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    APPLIED = "APPLIED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"

class FailureCategory(Enum):
    CLASSIFICATION_FAILURE = "CLASSIFICATION_FAILURE"
    PLANNING_FAILURE = "PLANNING_FAILURE"
    OPERATOR_UNAVAILABLE = "OPERATOR_UNAVAILABLE"
    OPERATOR_AMBIGUITY = "OPERATOR_AMBIGUITY"
    INVALID_PARAMETERS = "INVALID_PARAMETERS"
    STALE_PROPOSAL = "STALE_PROPOSAL"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    CAPABILITY_DENIED = "CAPABILITY_DENIED"
    SANDBOX_FAILURE = "SANDBOX_FAILURE"
    EXECUTION_FAILURE = "EXECUTION_FAILURE"
    VERIFICATION_FAILURE = "VERIFICATION_FAILURE"
    WORKSPACE_CHANGED = "WORKSPACE_CHANGED"
    TIMEOUT = "TIMEOUT"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    UNKNOWN = "UNKNOWN"

@dataclass
class EngineeringPlanStep:
    step_id: str
    order: int
    task_type: TaskType
    operator_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    affected_symbols: List[str] = field(default_factory=list)
    expected_changes: List[str] = field(default_factory=list)
    verification_profile: str = "PYTHON_SYNTAX_ONLY"
    risk_level: str = "LOW"
    status: PlanStepStatus = PlanStepStatus.PENDING

@dataclass
class EngineeringPlan:
    plan_id: str
    task_id: str
    repository_fingerprint: str
    task_classification: TaskClassification
    steps: List[EngineeringPlanStep] = field(default_factory=list)
    risk_level: str = "LOW"
    estimated_blast_radius: str = "LOW"
    required_capabilities: Set[ExecutionCapability] = field(default_factory=set)
    approval_required: bool = False
    created_at: float = field(default_factory=time.time)

@dataclass
class ExecutionResult:
    execution_id: str
    plan_id: str
    step_id: str
    transaction_id: str
    status: PlanStepStatus
    proposal_id: Optional[str] = None
    sandbox_result: Optional[Dict[str, Any]] = None
    verification_result: Optional[Dict[str, Any]] = None
    workspace_before_hash: Optional[str] = None
    workspace_after_hash: Optional[str] = None
    error: Optional[str] = None

@dataclass
class FailureDiagnosis:
    diagnosis_id: str
    execution_id: str
    failure_category: FailureCategory
    evidence: Dict[str, Any] = field(default_factory=dict)
    affected_step: Optional[str] = None
    retryable: bool = False
    recommended_action: str = ""

@dataclass
class OrchestrationReport:
    task_id: str
    request: str
    classification: Optional[Dict[str, Any]] = None
    repository_summary: Optional[Dict[str, Any]] = None
    plan: Optional[Dict[str, Any]] = None
    executed_steps: List[Dict[str, Any]] = field(default_factory=list)
    skipped_steps: List[Dict[str, Any]] = field(default_factory=list)
    verification_results: List[Dict[str, Any]] = field(default_factory=list)
    failures: List[Dict[str, Any]] = field(default_factory=list)
    retries: int = 0
    replans: int = 0
    workspace_changes: List[Dict[str, Any]] = field(default_factory=list)
    artifact_references: List[str] = field(default_factory=list)
    final_status: OrchestrationState = OrchestrationState.CREATED
    created_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None
