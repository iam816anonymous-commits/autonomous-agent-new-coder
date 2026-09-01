from typing import Dict, Any, List, Set
from repository.semantic.snapshot import SemanticRepositorySnapshot
from repository.semantic.models import SemanticSymbol, SemanticRelation

class DifferentialSemanticAnalyzer:
    """
    Compares two SemanticRepositorySnapshot instances to identify added, removed, modified, or unchanged symbols and call edges.
    """
    @classmethod
    def compare_snapshots(cls, previous: SemanticRepositorySnapshot, current: SemanticRepositorySnapshot) -> Dict[str, Any]:
        prev_sym_ids = set(previous.graph.symbols.keys())
        curr_sym_ids = set(current.graph.symbols.keys())

        added_syms = [current.graph.symbols[sid] for sid in (curr_sym_ids - prev_sym_ids)]
        removed_syms = [previous.graph.symbols[sid] for sid in (prev_sym_ids - curr_sym_ids)]

        modified_syms = []
        unchanged_syms = []

        common_ids = prev_sym_ids & curr_sym_ids
        for sid in sorted(list(common_ids)):
            p_sym = previous.graph.symbols[sid]
            c_sym = current.graph.symbols[sid]

            if p_sym.start_line != c_sym.start_line or p_sym.end_line != c_sym.end_line or p_sym.qualified_name != c_sym.qualified_name:
                modified_syms.append({"symbol_id": sid, "previous": p_sym, "current": c_sym})
            else:
                unchanged_syms.append(c_sym)

        return {
            "added_symbols": [s.symbol_id for s in added_syms],
            "removed_symbols": [s.symbol_id for s in removed_syms],
            "modified_symbols": [m["symbol_id"] for m in modified_syms],
            "unchanged_symbol_count": len(unchanged_syms),
            "summary": f"Added: {len(added_syms)}, Removed: {len(removed_syms)}, Modified: {len(modified_syms)}, Unchanged: {len(unchanged_syms)}"
        }
