from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import time

class CommandCategory(str, Enum):
    SYNTAX_CHECK = "SYNTAX_CHECK"
    TARGETED_TEST = "TARGETED_TEST"
    FULL_TEST = "FULL_TEST"
    LINT = "LINT"
    BUILD = "BUILD"
    FORMAT_CHECK = "FORMAT_CHECK"

class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    CRASHED = "CRASHED"
    OUTPUT_LIMIT_EXCEEDED = "OUTPUT_LIMIT_EXCEEDED"
    WORKSPACE_CHANGED = "WORKSPACE_CHANGED"

class VerificationStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    APPLIED_BUT_VERIFICATION_FAILED = "APPLIED_BUT_VERIFICATION_FAILED"
    WORKSPACE_CHANGED_DURING_VERIFICATION = "WORKSPACE_CHANGED_DURING_VERIFICATION"
    INCOMPLETE = "INCOMPLETE"
    DENIED = "DENIED"
    UNAVAILABLE = "UNAVAILABLE"

class ExecutionRiskLevel(str, Enum):
    LOW = "LOW"        # Static syntax/compilation checks
    MEDIUM = "MEDIUM"     # Read-only lint/formatting checks
    HIGH = "HIGH"       # Project test execution (arbitrary code run)

class ExecutionCapability(str, Enum):
    READ_WORKSPACE = "READ_WORKSPACE"
    WRITE_WORKSPACE = "WRITE_WORKSPACE"
    READ_ENVIRONMENT = "READ_ENVIRONMENT"
    NETWORK_ACCESS = "NETWORK_ACCESS"
    PROCESS_SPAWN = "PROCESS_SPAWN"

class VerificationLevel(str, Enum):
    NONE = "NONE"
    SYNTAX = "SYNTAX"
    TARGETED = "TARGETED"
    FULL = "FULL"

class ExecutionSideEffect(str, Enum):
    READ_ONLY = "READ_ONLY"
    WORKSPACE_WRITE = "WORKSPACE_WRITE"
    EXTERNAL_SIDE_EFFECT = "EXTERNAL_SIDE_EFFECT"

@dataclass
class CommandDefinition:
    name: str
    category: CommandCategory
    executable: str
    base_arguments: List[str] = field(default_factory=list)
    allowed_argument_patterns: List[str] = field(default_factory=list)
    allowed: bool = True
    timeout_seconds: float = 30.0
    risk_level: ExecutionRiskLevel = ExecutionRiskLevel.LOW
    capabilities: List[ExecutionCapability] = field(default_factory=lambda: [ExecutionCapability.READ_WORKSPACE, ExecutionCapability.PROCESS_SPAWN])
    side_effect: ExecutionSideEffect = ExecutionSideEffect.READ_ONLY
    description: str = ""

@dataclass
class CommandRequest:
    command_name: str
    extra_arguments: List[str] = field(default_factory=list)
    working_directory: Optional[str] = None

@dataclass
class ExecutionResult:
    command_id: str
    execution_id: str
    status: ExecutionStatus
    exit_code: int
    started_at: float
    finished_at: float
    duration: float
    stdout: str
    stderr: str
    resolved_executable: str = ""
    arguments: List[str] = field(default_factory=list)
    working_directory: str = "."
    policy_decision: str = "PERMITTED"
    workspace_snapshot_hash: Optional[str] = None
    environment_mode: str = "LOCAL_RESTRICTED"
    stdout_truncated: bool = False
    stderr_truncated: bool = False

@dataclass
class VerificationStep:
    step_id: str
    command_name: str
    category: CommandCategory
    required: bool = True
    risk_level: ExecutionRiskLevel = ExecutionRiskLevel.LOW
    description: str = ""
    extra_arguments: List[str] = field(default_factory=list)

@dataclass
class VerificationPlan:
    plan_id: str
    task_id: str
    steps: List[VerificationStep] = field(default_factory=list)
    estimated_duration: float = 0.0
    level: VerificationLevel = VerificationLevel.SYNTAX

@dataclass
class VerificationProfile:
    profile_id: str
    name: str
    description: str
    categories: List[CommandCategory] = field(default_factory=list)
    stop_on_failure: bool = True
    risk_level: ExecutionRiskLevel = ExecutionRiskLevel.LOW
    default_level: VerificationLevel = VerificationLevel.TARGETED

@dataclass
class VerificationResultModel:
    verification_id: str
    task_id: str
    status: VerificationStatus
    level: VerificationLevel = VerificationLevel.NONE
    step_results: List[ExecutionResult] = field(default_factory=list)
    rollback_executed: bool = False
    summary: str = ""
