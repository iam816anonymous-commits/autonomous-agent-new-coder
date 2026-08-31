"""
Controlled Verification Runtime package for Mini-Jules.
Executes predefined verification commands safely with zero shell access and risk-based execution approval boundaries.
"""

from .models import (
    CommandCategory,
    ExecutionStatus,
    VerificationStatus,
    ExecutionRiskLevel,
    CommandDefinition,
    CommandRequest,
    ExecutionResult,
    VerificationStep,
    VerificationPlan,
    VerificationResultModel
)
from .errors import (
    RuntimeException,
    CommandRejectedError,
    PolicyViolationError,
    ExecutionTimeoutError,
    WorkingDirectoryEscapeError,
    ExecutionApprovalRequiredError
)
from .policy import RuntimePolicy
from .command_registry import CommandRegistry
from .environment import ExecutionEnvironment, LocalRestrictedEnvironment
from .executor import CommandExecutor

__all__ = [
    "CommandCategory",
    "ExecutionStatus",
    "VerificationStatus",
    "ExecutionRiskLevel",
    "CommandDefinition",
    "CommandRequest",
    "ExecutionResult",
    "VerificationStep",
    "VerificationPlan",
    "VerificationResultModel",
    "RuntimeException",
    "CommandRejectedError",
    "PolicyViolationError",
    "ExecutionTimeoutError",
    "WorkingDirectoryEscapeError",
    "ExecutionApprovalRequiredError",
    "RuntimePolicy",
    "CommandRegistry",
    "ExecutionEnvironment",
    "LocalRestrictedEnvironment",
    "CommandExecutor"
]
