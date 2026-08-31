from typing import Dict, Any, List, Optional
from .graph import SemanticRepositoryGraph
from .models import SemanticRelationType, ConfidenceLevel

class ConservativeCallGraph:
    """
    Constructs a conservative call graph with explicit confidence levels:
    HIGH (AST unique local resolution), MEDIUM (unambiguous imported symbol), LOW (heuristic match), UNKNOWN (dynamic dispatch).
    """
    def __init__(self, graph: SemanticRepositoryGraph):
        self.graph = graph

    def get_callers(self, target_symbol_name: str) -> List[Dict[str, Any]]:
        callers = []
        for rel in self.graph.relations:
            if rel.relation_type == SemanticRelationType.CALLS:
                if rel.target_symbol_id.endswith(f":{target_symbol_name}") or rel.target_symbol_id == f"call:{target_symbol_name}":
                    src_sym = self.graph.get_symbol(rel.source_symbol_id)
                    callers.append({
                        "caller_symbol_id": rel.source_symbol_id,
                        "caller_name": src_sym.name if src_sym else rel.source_symbol_id,
                        "file_path": src_sym.file_path if src_sym else rel.evidence.file,
                        "line": rel.evidence.line,
                        "confidence": rel.confidence.value
                    })
        return callers
