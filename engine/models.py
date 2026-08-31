from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import time

SCHEMA_VERSION = 1

class TaskState(str, Enum):
    RECEIVED = "RECEIVED"
    ANALYZING = "ANALYZING"
    PLANNED = "PLANNED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    REPAIRING = "REPAIRING"
    REVERIFYING = "REVERIFYING"
    READY_TO_APPLY = "READY_TO_APPLY"
    APPLYING = "APPLYING"
    COMPLETED = "COMPLETED"

    # Terminal / Failure / Recovery States
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    ROLLED_BACK = "ROLLED_BACK"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"

class ActorType(str, Enum):
    SYSTEM = "SYSTEM"
    USER = "USER"
    AGENT = "AGENT"
    RECOVERY = "RECOVERY"

@dataclass
class TaskEvent:
    event_id: str
    task_id: str
    timestamp: float
    from_state: TaskState
    to_state: TaskState
    reason: str
    actor: ActorType = ActorType.SYSTEM
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskRecord:
    task_id: str
    repository_root: str
    request: str
    status: TaskState = TaskState.RECEIVED
    version: int = 1
    schema_version: int = SCHEMA_VERSION
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    base_commit: Optional[str] = None
    current_commit: Optional[str] = None
    working_branch: Optional[str] = None
    plan: Dict[str, Any] = field(default_factory=dict)
    risk: Dict[str, Any] = field(default_factory=dict)
    change_budget: Dict[str, Any] = field(default_factory=dict)
    expected_files: List[str] = field(default_factory=list)
    changed_files: List[str] = field(default_factory=list)
    test_results: Dict[str, Any] = field(default_factory=dict)
    security_results: Dict[str, Any] = field(default_factory=dict)
    repair_attempts: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    artifacts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    worker_id: Optional[str] = None
    lease_started_at: Optional[float] = None
    heartbeat_at: Optional[float] = None
