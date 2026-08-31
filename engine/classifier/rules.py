import re
from typing import List, Dict, Any, Optional, Tuple
from .models import TaskType, TaskClassificationStatus, TaskClassification
from .extraction import ParameterExtractor
from repository.models import BlastRadiusLevel

class ClassificationRule:
    """Base class for deterministic rule-based task classifiers."""
    def __init__(self, name: str, task_type: TaskType, priority: int = 10):
        self.name = name
        self.task_type = task_type
        self.priority = priority

    def matches(self, request: str, repo_snapshot=None) -> bool:
        raise NotImplementedError

    def evaluate(self, request: str, repo_snapshot=None) -> TaskClassification:
        raise NotImplementedError

def is_negated(text: str) -> bool:
    """Checks for explicit negation or prohibition in request."""
    patterns = [r"\bdo\s+not\b", r"\bdon'?t\b", r"\bnever\b", r"\bavoid\b", r"\bstop\b"]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)

def is_informational_question(text: str) -> bool:
    """Checks if request is asking an informational question rather than requesting execution."""
    patterns = [
        r"\bhow\s+to\b", r"\bshould\s+we\b", r"\bwhy\b", r"\bexplain\b",
        r"\bfind\s+out\b", r"\bwhat\s+is\b", r"\bcan\s+you\s+explain\b"
    ]
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)

def is_vague_request(text: str) -> bool:
    """Checks for generic/vague requests requiring clarification."""
    vague_patterns = [
        r"\bfix\s+(?:this\s+)?(?:project|code|repo|everything|all)?\b",
        r"\bimprove\s+(?:the\s+)?(?:code|project|app|everything|all)?\b",
        r"\bmake\s+(?:everything|this|it|code|api)\s+better\b",
        r"\bclean\s+(?:everything|up|code|project)\b",
        r"\boptimize\s+(?:it|this|code|project)?\b",
        r"\brefactor\s+(?:this\s+)?(?:code|project)?\b"
    ]
    # Check if vague phrase is present without specific targets (like symbol names or package names)
    if any(re.search(p, text, re.IGNORECASE) for p in vague_patterns):
        # Ensure it doesn't match specific commands like "Fix failing pytest tests" or "Rename foo to bar"
        if not re.search(r'\b(?:tests?|pytest|failing|to|from)\b', text, re.IGNORECASE):
            return True
    return False

class SymbolRenameRule(ClassificationRule):
    def __init__(self):
        super().__init__("SymbolRenameRule", TaskType.SYMBOL_RENAME, priority=20)

    def matches(self, request: str, repo_snapshot=None) -> bool:
        if is_negated(request): return False
        if is_informational_question(request): return False
        return bool(ParameterExtractor.extract_symbol_rename(request))

    def evaluate(self, request: str, repo_snapshot=None) -> TaskClassification:
        params = ParameterExtractor.extract_symbol_rename(request) or {}
        evidence = ["Found rename syntax pattern", f"Old symbol: {params.get('old_name')}", f"New symbol: {params.get('new_name')}"]
        capabilities = ["repository.symbols", "filesystem.read", "filesystem.write", "verification.tests"]

        confidence = 0.95
        warnings = []

        if repo_snapshot and "old_name" in params:
            syms = repo_snapshot.symbols.find_symbol(params["old_name"])
            if syms:
                evidence.append(f"Confirmed symbol '{params['old_name']}' exists in {len(syms)} location(s) in repository.")
            else:
                confidence = 0.70
                warnings.append(f"Requested symbol '{params['old_name']}' was not found in repository index.")

        return TaskClassification(
            task_type=TaskType.SYMBOL_RENAME,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=confidence,
            extracted_parameters=params,
            evidence=evidence,
            required_capabilities=capabilities,
            risk=BlastRadiusLevel.LOW,
            warnings=warnings
        )

class DependencyUpgradeRule(ClassificationRule):
    def __init__(self):
        super().__init__("DependencyUpgradeRule", TaskType.DEPENDENCY_UPGRADE, priority=20)

    def matches(self, request: str, repo_snapshot=None) -> bool:
        if is_negated(request) or is_informational_question(request): return False
        params = ParameterExtractor.extract_dependency_upgrade(request)
        return bool(params and params.get("package"))

    def evaluate(self, request: str, repo_snapshot=None) -> TaskClassification:
        params = ParameterExtractor.extract_dependency_upgrade(request) or {}
        evidence = ["Found dependency upgrade pattern", f"Package: {params.get('package')}", f"Version: {params.get('target_version')}"]
        capabilities = ["repository.package_manager", "filesystem.read", "filesystem.write", "verification.tests"]

        return TaskClassification(
            task_type=TaskType.DEPENDENCY_UPGRADE,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=0.95,
            extracted_parameters=params,
            evidence=evidence,
            required_capabilities=capabilities,
            risk=BlastRadiusLevel.MEDIUM
        )

class DependencyChangeRule(ClassificationRule):
    def __init__(self):
        super().__init__("DependencyChangeRule", TaskType.DEPENDENCY_CHANGE, priority=18)

    def matches(self, request: str, repo_snapshot=None) -> bool:
        if is_negated(request) or is_informational_question(request): return False
        return bool(ParameterExtractor.extract_dependency_change(request))

    def evaluate(self, request: str, repo_snapshot=None) -> TaskClassification:
        params = ParameterExtractor.extract_dependency_change(request) or {}
        evidence = ["Found dependency modification pattern", f"Params: {params}"]
        capabilities = ["repository.package_manager", "filesystem.read", "filesystem.write", "verification.tests"]

        return TaskClassification(
            task_type=TaskType.DEPENDENCY_CHANGE,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=0.90,
            extracted_parameters=params,
            evidence=evidence,
            required_capabilities=capabilities,
            risk=BlastRadiusLevel.MEDIUM
        )

class FileMoveRule(ClassificationRule):
    def __init__(self):
        super().__init__("FileMoveRule", TaskType.FILE_MOVE, priority=20)

    def matches(self, request: str, repo_snapshot=None) -> bool:
        if is_negated(request) or is_informational_question(request): return False
        return bool(ParameterExtractor.extract_file_move(request))

    def evaluate(self, request: str, repo_snapshot=None) -> TaskClassification:
        params = ParameterExtractor.extract_file_move(request) or {}
        evidence = ["Found file move pattern", f"Source: {params.get('source')}", f"Destination: {params.get('destination')}"]
        capabilities = ["filesystem.read", "filesystem.write", "git.move"]

        return TaskClassification(
            task_type=TaskType.FILE_MOVE,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=0.95,
            extracted_parameters=params,
            evidence=evidence,
            required_capabilities=capabilities,
            risk=BlastRadiusLevel.LOW
        )

class RouteExtensionRule(ClassificationRule):
    def __init__(self):
        super().__init__("RouteExtensionRule", TaskType.ROUTE_EXTENSION, priority=20)

    def matches(self, request: str, repo_snapshot=None) -> bool:
        if is_negated(request) or is_informational_question(request): return False
        return bool(ParameterExtractor.extract_route(request))

    def evaluate(self, request: str, repo_snapshot=None) -> TaskClassification:
        params = ParameterExtractor.extract_route(request) or {}
        evidence = ["Found route addition pattern", f"Method: {params.get('http_method')}", f"Route: {params.get('route')}"]
        capabilities = ["filesystem.read", "filesystem.write", "verification.tests"]

        return TaskClassification(
            task_type=TaskType.ROUTE_EXTENSION,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=0.95,
            extracted_parameters=params,
            evidence=evidence,
            required_capabilities=capabilities,
            risk=BlastRadiusLevel.MEDIUM
        )

class CrudExtensionRule(ClassificationRule):
    def __init__(self):
        super().__init__("CrudExtensionRule", TaskType.CRUD_EXTENSION, priority=18)

    def matches(self, request: str, repo_snapshot=None) -> bool:
        if is_negated(request) or is_informational_question(request): return False
        return bool(ParameterExtractor.extract_crud(request))

    def evaluate(self, request: str, repo_snapshot=None) -> TaskClassification:
        params = ParameterExtractor.extract_crud(request) or {}
        evidence = ["Found CRUD extension pattern", f"Resource: {params.get('resource')}"]
        capabilities = ["filesystem.read", "filesystem.write", "verification.tests"]

        return TaskClassification(
            task_type=TaskType.CRUD_EXTENSION,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=0.90,
            extracted_parameters=params,
            evidence=evidence,
            required_capabilities=capabilities,
            risk=BlastRadiusLevel.MEDIUM
        )

class CodeFormattingRule(ClassificationRule):
    def __init__(self):
        super().__init__("CodeFormattingRule", TaskType.CODE_FORMATTING, priority=15)

    def matches(self, request: str, repo_snapshot=None) -> bool:
        if is_negated(request) or is_informational_question(request): return False
        return bool(re.search(r'\b(?:format|run\s+formatting|fix\s+formatting)\b', request, re.IGNORECASE))

    def evaluate(self, request: str, repo_snapshot=None) -> TaskClassification:
        return TaskClassification(
            task_type=TaskType.CODE_FORMATTING,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=0.95,
            extracted_parameters={},
            evidence=["Found code formatting request"],
            required_capabilities=["filesystem.write", "process.format"],
            risk=BlastRadiusLevel.LOW
        )

class TestRepairRule(ClassificationRule):
    def __init__(self):
        super().__init__("TestRepairRule", TaskType.TEST_REPAIR, priority=15)

    def matches(self, request: str, repo_snapshot=None) -> bool:
        if is_negated(request) or is_informational_question(request): return False
        return bool(re.search(r'\b(?:fix|repair|make)\s+(?:failing\s+)?(?:tests?|pytest|suite)\s*(?:pass|failing)?\b', request, re.IGNORECASE))

    def evaluate(self, request: str, repo_snapshot=None) -> TaskClassification:
        return TaskClassification(
            task_type=TaskType.TEST_REPAIR,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=0.90,
            extracted_parameters={},
            evidence=["Found test repair request"],
            required_capabilities=["filesystem.write", "verification.tests"],
            risk=BlastRadiusLevel.MEDIUM
        )

class AnalysisOnlyRule(ClassificationRule):
    def __init__(self):
        super().__init__("AnalysisOnlyRule", TaskType.ANALYSIS_ONLY, priority=25)

    def matches(self, request: str, repo_snapshot=None) -> bool:
        if is_informational_question(request): return True
        return bool(re.search(r'\b(?:analyze|show|explain|find\s+circular|find\s+unused)\b', request, re.IGNORECASE))

    def evaluate(self, request: str, repo_snapshot=None) -> TaskClassification:
        return TaskClassification(
            task_type=TaskType.ANALYSIS_ONLY,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=0.95,
            extracted_parameters={"raw_request": request},
            evidence=["Found analysis/informational request pattern"],
            required_capabilities=["repository.scan", "repository.symbols", "repository.dependencies"],
            risk=BlastRadiusLevel.LOW
        )

class MigrationRule(ClassificationRule):
    def __init__(self):
        super().__init__("MigrationRule", TaskType.MIGRATION, priority=15)

    def matches(self, request: str, repo_snapshot=None) -> bool:
        if is_negated(request) or is_informational_question(request): return False
        return bool(ParameterExtractor.extract_migration(request))

    def evaluate(self, request: str, repo_snapshot=None) -> TaskClassification:
        params = ParameterExtractor.extract_migration(request) or {}
        return TaskClassification(
            task_type=TaskType.MIGRATION,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=0.85,
            extracted_parameters=params,
            evidence=["Found migration request pattern", f"Params: {params}"],
            required_capabilities=["filesystem.write", "verification.tests"],
            risk=BlastRadiusLevel.HIGH
        )

class TemplateGenerationRule(ClassificationRule):
    def __init__(self):
        super().__init__("TemplateGenerationRule", TaskType.TEMPLATE_GENERATION, priority=15)

    def matches(self, request: str, repo_snapshot=None) -> bool:
        if is_negated(request) or is_informational_question(request): return False
        return bool(re.search(r'\b(?:create|generate)\s+a?\s*([a-zA-Z0-9_-]+)?\s*(?:project|template)\b', request, re.IGNORECASE))

    def evaluate(self, request: str, repo_snapshot=None) -> TaskClassification:
        return TaskClassification(
            task_type=TaskType.TEMPLATE_GENERATION,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=0.90,
            extracted_parameters={},
            evidence=["Found project/template generation request"],
            required_capabilities=["filesystem.write"],
            risk=BlastRadiusLevel.MEDIUM
        )

class DocumentationUpdateRule(ClassificationRule):
    def __init__(self):
        super().__init__("DocumentationUpdateRule", TaskType.DOCUMENTATION_UPDATE, priority=15)

    def matches(self, request: str, repo_snapshot=None) -> bool:
        if is_negated(request) or is_informational_question(request): return False
        return bool(re.search(r'\b(?:update|document|add\s+docs\s+for)\s+(?:readme|docs|documentation|api)\b', request, re.IGNORECASE))

    def evaluate(self, request: str, repo_snapshot=None) -> TaskClassification:
        return TaskClassification(
            task_type=TaskType.DOCUMENTATION_UPDATE,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=0.95,
            extracted_parameters={},
            evidence=["Found documentation update request"],
            required_capabilities=["filesystem.write"],
            risk=BlastRadiusLevel.LOW
        )

# Registry of default rules
ALL_RULES: List[ClassificationRule] = [
    AnalysisOnlyRule(),
    SymbolRenameRule(),
    DependencyUpgradeRule(),
    DependencyChangeRule(),
    FileMoveRule(),
    RouteExtensionRule(),
    CrudExtensionRule(),
    CodeFormattingRule(),
    TestRepairRule(),
    MigrationRule(),
    TemplateGenerationRule(),
    DocumentationUpdateRule()
]
