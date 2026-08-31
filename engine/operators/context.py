import os
import uuid
from dataclasses import dataclass, field
from typing import Optional, Any
from engine.classifier.models import TaskClassification
from repository.scan import RepositorySnapshot

@dataclass
class OperatorContext:
    repository_root: str
    task_id: str
    classification: TaskClassification
    repo_snapshot: Optional[RepositorySnapshot] = None
    transaction_id: str = field(default_factory=lambda: f"OP-{uuid.uuid4().hex[:10]}")

    def __post_init__(self):
        self.repository_root = os.path.realpath(os.path.abspath(self.repository_root))
