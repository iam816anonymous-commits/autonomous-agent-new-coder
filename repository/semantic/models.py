from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

class SymbolKind(str, Enum):
    MODULE = "MODULE"
    PACKAGE = "PACKAGE"
    CLASS = "CLASS"
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    VARIABLE = "VARIABLE"
    PARAMETER = "PARAMETER"
    IMPORT = "IMPORT"
    ROUTE = "ROUTE"
    TEST = "TEST"
    UNKNOWN = "UNKNOWN"

class SemanticRelationType(str, Enum):
    DEFINES = "DEFINES"
    REFERENCES = "REFERENCES"
    IMPORTS = "IMPORTS"
    CALLS = "CALLS"
    INHERITS = "INHERITS"
    IMPLEMENTS = "IMPLEMENTS"
    CONTAINS = "CONTAINS"
    EXPORTS = "EXPORTS"
    DECORATES = "DECORATES"
    TESTS = "TESTS"
    ROUTES_TO = "ROUTES_TO"
    READS = "READS"
    WRITES = "WRITES"
    UNKNOWN = "UNKNOWN"

class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"

class ArchitecturePattern(str, Enum):
    LAYERED = "LAYERED"
    MVC = "MVC"
    SERVICE_REPOSITORY = "SERVICE_REPOSITORY"
    API_CONTROLLER = "API_CONTROLLER"
    UNKNOWN = "UNKNOWN"

@dataclass
class Evidence:
    file: str
    line: int = 0
    extraction_mechanism: str = "AST"
    confidence_reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SemanticSymbol:
    symbol_id: str
    name: str
    qualified_name: str
    symbol_kind: SymbolKind
    language: str
    file_path: str
    start_line: int = 0
    end_line: int = 0
    parent_symbol_id: Optional[str] = None
    visibility: str = "public"
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH

@dataclass
class SemanticRelation:
    source_symbol_id: str
    target_symbol_id: str
    relation_type: SemanticRelationType
    evidence: Evidence
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH

@dataclass
class SemanticImpactReport:
    target_symbol: str
    directly_affected_symbols: List[str] = field(default_factory=list)
    transitively_affected_symbols: List[str] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)
    affected_tests: List[str] = field(default_factory=list)
    architectural_boundaries_crossed: List[str] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    blast_radius: str = "LOW"
    blast_radius_score: int = 0
