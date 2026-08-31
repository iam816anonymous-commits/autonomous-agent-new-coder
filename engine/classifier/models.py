from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from repository.models import BlastRadiusLevel

class TaskType(str, Enum):
    DEPENDENCY_UPGRADE = "DEPENDENCY_UPGRADE"
    DEPENDENCY_CHANGE = "DEPENDENCY_CHANGE"
    SYMBOL_RENAME = "SYMBOL_RENAME"
    IMPORT_CHANGE = "IMPORT_CHANGE"
    FILE_MOVE = "FILE_MOVE"
    FILE_RENAME = "FILE_RENAME"
    CRUD_EXTENSION = "CRUD_EXTENSION"
    ROUTE_EXTENSION = "ROUTE_EXTENSION"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    TEST_REPAIR = "TEST_REPAIR"
    CODE_FORMATTING = "CODE_FORMATTING"
    MIGRATION = "MIGRATION"
    REFACTORING = "REFACTORING"
    TEMPLATE_GENERATION = "TEMPLATE_GENERATION"
    DOCUMENTATION_UPDATE = "DOCUMENTATION_UPDATE"
    ANALYSIS_ONLY = "ANALYSIS_ONLY"
    COMPOSITE_TASK = "COMPOSITE_TASK"

    # Fallback / Special
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"

class TaskClassificationStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"

@dataclass
class TaskClassification:
    task_type: TaskType
    status: TaskClassificationStatus
    confidence: float
    extracted_parameters: Dict[str, Any] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    required_capabilities: List[str] = field(default_factory=list)
    risk: BlastRadiusLevel = BlastRadiusLevel.LOW
    warnings: List[str] = field(default_factory=list)
    subtasks: List['TaskClassification'] = field(default_factory=list)
