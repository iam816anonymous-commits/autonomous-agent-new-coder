from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import time

class WorkflowStatus(Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    REPLAYING = "REPLAYING"

class StepStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"

class ReplayMode(Enum):
    DRY_RUN = "DRY_RUN"
    VALIDATION_ONLY = "VALIDATION_ONLY"
    FULL_REPLAY = "FULL_REPLAY"

@dataclass
class Checkpoint:
    checkpoint_id: str
    workflow_id: str
    task_id: str
    sequence_number: int
    timestamp: float
    workflow_status: WorkflowStatus
    current_step: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)
    pending_steps: List[str] = field(default_factory=list)
    workspace_fingerprint: str = ""
    plan_fingerprint: str = ""
    execution_state: Dict[str, Any] = field(default_factory=dict)
    previous_checkpoint_id: Optional[str] = None

@dataclass
class WorkflowExecution:
    workflow_id: str
    task_id: str
    orchestration_run_id: str
    plan_id: str
    status: WorkflowStatus
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    current_checkpoint_id: Optional[str] = None
    workspace_fingerprint: str = ""
    plan_fingerprint: str = ""
    retry_count: int = 0
    replay_of_workflow_id: Optional[str] = None

@dataclass
class StepExecution:
    step_execution_id: str
    workflow_id: str
    step_id: str
    operator_name: str
    status: StepStatus
    proposal_id: Optional[str] = None
    transaction_id: Optional[str] = None
    attempt_number: int = 1
    input_fingerprint: str = ""
    output_fingerprint: Optional[str] = None
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    error: Optional[str] = None

@dataclass
class ReplayRequest:
    source_workflow_id: str
    requested_by: str
    replay_mode: ReplayMode
    expected_workspace_fingerprint: str = ""
    expected_plan_fingerprint: str = ""
