from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from enum import Enum

class SymbolType(str, Enum):
    FUNCTION = "function"
    ASYNC_FUNCTION = "async_function"
    CLASS = "class"
    METHOD = "method"
    IMPORT = "import"
    EXPORT = "export"
    VARIABLE = "variable"

class DependencyType(str, Enum):
    LOCAL_FILE = "local_file"
    STDLIB = "stdlib"
    THIRD_PARTY = "third_party"
    UNKNOWN = "unknown"

class BlastRadiusLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class Symbol:
    name: str
    symbol_type: SymbolType
    file_path: str
    line: int = 0
    column: int = 0
    container: str = "global"

@dataclass
class SymbolReference:
    symbol_name: str
    file_path: str
    line: int = 0
    column: int = 0
    container: str = "global"

@dataclass
class DependencyEdge:
    source: str
    target: str
    dependency_type: DependencyType = DependencyType.LOCAL_FILE
    symbol_name: Optional[str] = None

@dataclass
class FileInfo:
    path: str
    language: Optional[str] = None
    is_test: bool = False
    is_entry_point: bool = False
    is_binary: bool = False
    file_size: int = 0

@dataclass
class RepositoryInfo:
    root: str
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    package_managers: List[str] = field(default_factory=list)
    source_files: List[str] = field(default_factory=list)
    test_files: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)

@dataclass
class DependencyGraphModel:
    nodes: List[str] = field(default_factory=list)
    edges: List[DependencyEdge] = field(default_factory=list)
    cycles: List[List[str]] = field(default_factory=list)
    unresolved_imports: List[Dict[str, str]] = field(default_factory=list)

@dataclass
class ImpactReport:
    changed_file: str
    direct_dependents: List[str] = field(default_factory=list)
    transitive_dependents: List[str] = field(default_factory=list)
    related_symbols: List[str] = field(default_factory=list)
    related_tests: List[str] = field(default_factory=list)
    blast_radius: BlastRadiusLevel = BlastRadiusLevel.LOW
    blast_radius_score: int = 0
