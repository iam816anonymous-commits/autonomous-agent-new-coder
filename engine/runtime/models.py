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

class VerificationStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"

class ExecutionRiskLevel(str, Enum):
    LOW = "LOW"        # Static syntax/compilation checks
    MEDIUM = "MEDIUM"     # Read-only lint/formatting checks
    HIGH = "HIGH"       # Project test execution (arbitrary code run)

@dataclass
class CommandDefinition:
    name: str
    category: CommandCategory
    executable: str
    base_arguments: List[str] = field(default_factory=list)
    allowed: bool = True
    timeout_seconds: float = 30.0
    risk_level: ExecutionRiskLevel = ExecutionRiskLevel.LOW

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

@dataclass
class VerificationResultModel:
    verification_id: str
    task_id: str
    status: VerificationStatus
    step_results: List[ExecutionResult] = field(default_factory=list)
    rollback_executed: bool = False
    summary: str = ""
