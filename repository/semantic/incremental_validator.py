from typing import List, Dict, Any
from repository.semantic.snapshot import SemanticRepositorySnapshot, SemanticSnapshotter
from repository.semantic.incremental import IncrementalSemanticAnalyzer
from repository.scan import RepositorySnapshot

class IncrementalSemanticValidator:
    """
    Compares full re-analysis vs incremental analysis outputs to detect divergence and force full rebuild fallback if needed.
    """
    @classmethod
    def validate_incremental_update(
        cls,
        base_snapshot: SemanticRepositorySnapshot,
        repo_snapshot: RepositorySnapshot,
        changed_files: List[str]
    ) -> Dict[str, Any]:
        # 1. Compute incremental update
        incremental_snap = IncrementalSemanticAnalyzer.update_snapshot(base_snapshot, repo_snapshot, changed_files)

        # 2. Compute ground-truth full rebuild
        full_snap = SemanticSnapshotter.capture(repo_snapshot)

        # 3. Compare symbol count and identities
        inc_ids = set(incremental_snap.graph.symbols.keys())
        full_ids = set(full_snap.graph.symbols.keys())

        if inc_ids == full_ids:
            return {
                "status": "INCREMENTAL_MATCH",
                "divergence_count": 0,
                "used_snapshot": incremental_snap
            }

        divergence = len(inc_ids ^ full_ids)
        return {
            "status": "INCREMENTAL_DIVERGENCE",
            "divergence_count": divergence,
            "fallback_required": True,
            "used_snapshot": full_snap
        }
