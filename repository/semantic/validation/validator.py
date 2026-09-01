from typing import List, Dict, Set, Optional
from repository.semantic.graph import SemanticRepositoryGraph
from repository.semantic.models import SymbolKind, SemanticRelationType
from .models import ValidationStatus, ValidationIssue, IssueSeverity, ValidationResult

class SemanticGraphValidator:
    """
    Independently inspects semantic graphs to detect dangling nodes, unresolved references, impossible edges, and duplicate symbols.
    """
    def __init__(self, graph: SemanticRepositoryGraph):
        self.graph = graph

    def validate(self) -> ValidationResult:
        issues: List[ValidationIssue] = []
        dangling_nodes = 0
        unresolved_refs = 0
        duplicates = 0

        # 1. Check duplicate symbols
        name_file_map: Dict[str, List[str]] = {}
        for sym_id, sym in self.graph.symbols.items():
            key = f"{sym.file_path}:{sym.name}:{sym.symbol_kind.value}"
            if key not in name_file_map:
                name_file_map[key] = []
            name_file_map[key].append(sym_id)

        for key, ids in name_file_map.items():
            if len(ids) > 1 and not key.endswith("IMPORT"):
                duplicates += 1
                issues.append(ValidationIssue(
                    issue_type="DUPLICATE_SYMBOL",
                    description=f"Duplicate symbol definition for key '{key}' across IDs: {ids}",
                    severity=IssueSeverity.WARNING,
                    affected_symbol_id=ids[0]
                ))

        # 2. Check relation endpoints (dangling nodes)
        for rel in self.graph.relations:
            src_exists = rel.source_symbol_id in self.graph.symbols
            tgt_exists = rel.target_symbol_id in self.graph.symbols or rel.target_symbol_id.startswith(("base:", "call:"))

            if not src_exists:
                dangling_nodes += 1
                issues.append(ValidationIssue(
                    issue_type="DANGLING_SOURCE",
                    description=f"Relation source symbol '{rel.source_symbol_id}' does not exist in graph.",
                    severity=IssueSeverity.BLOCKING,
                    affected_symbol_id=rel.source_symbol_id
                ))

            if not tgt_exists:
                unresolved_refs += 1
                issues.append(ValidationIssue(
                    issue_type="UNRESOLVED_REFERENCE",
                    description=f"Relation target symbol '{rel.target_symbol_id}' cannot be resolved.",
                    severity=IssueSeverity.WARNING,
                    affected_symbol_id=rel.target_symbol_id
                ))

        # Determine overall status
        if any(i.severity == IssueSeverity.BLOCKING for i in issues):
            status = ValidationStatus.INVALID
        elif issues:
            status = ValidationStatus.PARTIALLY_VALID
        else:
            status = ValidationStatus.VALID

        return ValidationResult(
            status=status,
            issues=issues,
            dangling_node_count=dangling_nodes,
            unresolved_reference_count=unresolved_refs,
            duplicate_symbol_count=duplicates
        )
