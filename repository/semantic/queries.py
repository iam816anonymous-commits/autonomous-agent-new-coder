from typing import Dict, Any, List, Optional
from .graph import SemanticRepositoryGraph
from .call_graph import ConservativeCallGraph
from .models import ConfidenceLevel

class SemanticQueryEngine:
    """
    Exposes high-level semantic queries: who_calls, what_does_this_call, symbol_dependencies, and implementation_path.
    """
    def __init__(self, graph: SemanticRepositoryGraph):
        self.graph = graph
        self.call_graph = ConservativeCallGraph(graph)

    def who_calls(self, symbol_name: str) -> List[Dict[str, Any]]:
        return self.call_graph.get_callers(symbol_name)

    def what_does_this_call(self, symbol_id: str) -> List[Dict[str, Any]]:
        callees = []
        for rel in self.graph.outgoing_relations(symbol_id):
            if rel.relation_type.value == "CALLS":
                callees.append({
                    "target_symbol_id": rel.target_symbol_id,
                    "confidence": rel.confidence.value,
                    "file": rel.evidence.file,
                    "line": rel.evidence.line
                })
        return callees

    def symbol_dependencies(self, symbol_id: str) -> List[str]:
        deps = set()
        for rel in self.graph.outgoing_relations(symbol_id):
            deps.add(rel.target_symbol_id)
        return sorted(list(deps))

    def implementation_path(self, request_description: str) -> Dict[str, Any]:
        """
        Calculates a likely implementation path based on request keywords and indexed symbols.
        """
        matched_symbols = []
        for sym_id, sym in self.graph.symbols.items():
            if sym.name.lower() in request_description.lower():
                matched_symbols.append(sym)

        affected_files = sorted(list(set([s.file_path for s in matched_symbols])))
        confidence = ConfidenceLevel.HIGH if len(matched_symbols) == 1 else (ConfidenceLevel.MEDIUM if len(matched_symbols) > 1 else ConfidenceLevel.LOW)

        return {
            "query": request_description,
            "matched_symbols": [s.name for s in matched_symbols],
            "affected_files": affected_files,
            "confidence": confidence.value
        }
