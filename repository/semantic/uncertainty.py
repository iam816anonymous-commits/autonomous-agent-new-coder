from typing import Set, Dict, List
from repository.semantic.graph import SemanticRepositoryGraph
from repository.semantic.models import ConfidenceLevel, SemanticRelationType

class UncertaintyPropagator:
    """
    Propagates confidence reductions through incoming call graph relationships using bounded traversal.
    """
    @classmethod
    def propagate_uncertainty(cls, graph: SemanticRepositoryGraph, max_depth: int = 5) -> int:
        degraded_count = 0
        low_confidence_nodes: Set[str] = set()

        for sym_id, sym in graph.symbols.items():
            if sym.confidence in (ConfidenceLevel.LOW, ConfidenceLevel.UNKNOWN):
                low_confidence_nodes.add(sym_id)

        queue: List[str] = list(low_confidence_nodes)
        visited: Set[str] = set(low_confidence_nodes)

        depth = 0
        while queue and depth < max_depth:
            depth += 1
            next_queue = []
            for node_id in queue:
                # Find incoming call relations (callers of low-confidence symbol)
                for rel in graph.incoming_relations(node_id):
                    if rel.relation_type == SemanticRelationType.CALLS:
                        caller_sym = graph.get_symbol(rel.source_symbol_id)
                        if caller_sym and caller_sym.confidence == ConfidenceLevel.HIGH:
                            caller_sym.confidence = ConfidenceLevel.MEDIUM
                            rel.confidence = ConfidenceLevel.MEDIUM
                            degraded_count += 1
                            if caller_sym.symbol_id not in visited:
                                visited.add(caller_sym.symbol_id)
                                next_queue.append(caller_sym.symbol_id)
            queue = next_queue

        return degraded_count
