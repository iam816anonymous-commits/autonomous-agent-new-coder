"""
Engineering Operators package for Mini-Jules.
Executes deterministic code modifications offline with dry-run, SHA256 integrity, and approval boundaries.
"""

from .models import (
    Precondition,
    FileChange,
    OperatorPlan,
    ProposedChange,
    VerificationResult,
    ApplyResult
)
from .context import OperatorContext
from .errors import (
    OperatorError,
    PreconditionFailedError,
    StaleProposalError,
    ApprovalRequiredError,
    RollbackError
)
from .base import EngineeringOperator, compute_sha256
from .registry import OperatorRegistry

__all__ = [
    "Precondition",
    "FileChange",
    "OperatorPlan",
    "ProposedChange",
    "VerificationResult",
    "ApplyResult",
    "OperatorContext",
    "OperatorError",
    "PreconditionFailedError",
    "StaleProposalError",
    "ApprovalRequiredError",
    "RollbackError",
    "EngineeringOperator",
    "compute_sha256",
    "OperatorRegistry"
]
