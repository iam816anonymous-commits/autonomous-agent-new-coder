from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from repository.models import BlastRadiusLevel

@dataclass
class Precondition:
    name: str
    satisfied: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class FileChange:
    path: str
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    old_sha256: Optional[str] = None
    new_sha256: Optional[str] = None
    diff: str = ""

@dataclass
class OperatorPlan:
    operator_name: str
    task_id: str
    steps: List[str] = field(default_factory=list)
    estimated_risk: BlastRadiusLevel = BlastRadiusLevel.LOW
    preconditions: List[Precondition] = field(default_factory=list)

@dataclass
class ProposedChange:
    operator_name: str
    transaction_id: str
    task_id: str
    files_to_modify: List[FileChange] = field(default_factory=list)
    files_to_create: List[FileChange] = field(default_factory=list)
    files_to_delete: List[str] = field(default_factory=list)
    preconditions: List[Precondition] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    risk: BlastRadiusLevel = BlastRadiusLevel.LOW

@dataclass
class VerificationResult:
    passed: bool
    checks_run: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)

@dataclass
class ApplyResult:
    success: bool
    transaction_id: str
    files_modified: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    files_deleted: List[str] = field(default_factory=list)
    rollback_available: bool = True
    error: Optional[str] = None
