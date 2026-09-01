from typing import Dict, Any, List, Set
from repository.semantic.snapshot import SemanticRepositorySnapshot
from repository.semantic.graph import SemanticRepositoryGraph
from repository.semantic.models import ConfidenceLevel, Evidence
from .models import ChangeRequest

class ChangeImpactAnalyzer:
    """
    Evaluates direct impact, transitive call impact, affected tests, and architectural boundary crossings for a ChangeRequest.
    """
    def __init__(self, semantic_snapshot: SemanticRepositorySnapshot):
        self.snapshot = semantic_snapshot
        self.graph = semantic_snapshot.graph

    def analyze_change_impact(self, request: ChangeRequest, target_symbols: List[str]) -> Dict[str, Any]:
        direct_symbols: Set[str] = set(target_symbols)
        transitive_symbols: Set[str] = set()
        affected_files: Set[str] = set()
        affected_tests: Set[str] = set()
        boundaries_crossed: Set[str] = set()

        for sym_name in target_symbols:
            for s in self.graph.find_symbols(sym_name):
                affected_files.add(s.file_path)
                # Find transitive dependents via incoming relations
                for dep in self.graph.affected_symbols(s.symbol_id):
                    transitive_symbols.add(dep.name)
                    affected_files.add(dep.file_path)
                    if "test" in dep.file_path.lower():
                        affected_tests.add(dep.file_path)

        # Detect architectural boundary crossings
        file_paths_str = " ".join(affected_files).lower()
        if "api" in file_paths_str or "controller" in file_paths_str:
            boundaries_crossed.add("API_LAYER")
        if "service" in file_paths_str:
            boundaries_crossed.add("SERVICE_LAYER")
        if "repo" in file_paths_str or "db" in file_paths_str or "store" in file_paths_str:
            boundaries_crossed.add("DATABASE_LAYER")

        risk = "HIGH" if len(boundaries_crossed) >= 2 or len(affected_files) >= 5 else ("MEDIUM" if len(affected_files) >= 2 else "LOW")

        return {
            "request_id": request.request_id,
            "direct_symbols": sorted(list(direct_symbols)),
            "transitive_symbols": sorted(list(transitive_symbols - direct_symbols)),
            "affected_files": sorted(list(affected_files)),
            "affected_tests": sorted(list(affected_tests)),
            "architectural_boundaries_crossed": sorted(list(boundaries_crossed)),
            "risk_level": risk,
            "confidence": ConfidenceLevel.HIGH if len(affected_files) > 0 else ConfidenceLevel.LOW
        }
