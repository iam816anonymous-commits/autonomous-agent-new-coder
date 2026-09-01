from typing import List, Set, Dict, Any
from repository.semantic.snapshot import SemanticRepositorySnapshot
from repository.semantic.differential import DifferentialSemanticAnalyzer
from .models import ChangePlan, ChangeOutcome

class ChangeOutcomeAnalyzer:
    """
    Compares expected modifications against actual repository changes using semantic snapshot differencing.
    Detects unexpected file/symbol modifications or broken call paths.
    """
    @classmethod
    def compare_expected_vs_actual(
        cls,
        plan: ChangePlan,
        snapshot_before: SemanticRepositorySnapshot,
        snapshot_after: SemanticRepositorySnapshot
    ) -> ChangeOutcome:
        diff = DifferentialSemanticAnalyzer.compare_snapshots(snapshot_before, snapshot_after)

        expected_files: Set[str] = set()
        expected_symbols: Set[str] = set()

        for step in plan.steps:
            expected_files.update(step.target_files)
            expected_symbols.update(step.target_symbols)

        actual_symbols = set(diff["modified_symbols"]) | set(diff["added_symbols"])
        unexpected_symbols = [s for s in actual_symbols if s not in expected_symbols and not any(exp in s for exp in expected_symbols)]

        # Extract actual modified file paths from snapshot_after for symbols in actual_symbols
        actual_files: Set[str] = set()
        for sid in actual_symbols:
            sym = snapshot_after.graph.get_symbol(sid)
            if sym:
                actual_files.add(sym.file_path)

        unexpected_files = [f for f in actual_files if f not in expected_files]

        # Check architectural violations in added/modified relations
        arch_violations = []
        if diff["added_symbols"]:
            patterns_after = snapshot_after.architecture.get("patterns", [])
            patterns_before = snapshot_before.architecture.get("patterns", [])
            if "UNKNOWN" in patterns_after and "UNKNOWN" not in patterns_before:
                arch_violations.append("Architectural pattern degraded to UNKNOWN after change.")

        match_status = "VIOLATION" if arch_violations else ("UNEXPECTED_CHANGE" if (unexpected_symbols or unexpected_files) else "MATCH")

        return ChangeOutcome(
            plan_id=plan.plan_id,
            expected_modified_files=sorted(list(expected_files)),
            actual_modified_files=sorted(list(actual_files if actual_files else expected_files)),
            unexpected_modified_files=sorted(unexpected_files),
            expected_symbols=sorted(list(expected_symbols)),
            actual_symbols=sorted(list(actual_symbols)),
            unexpected_symbols=sorted(unexpected_symbols),
            architectural_violations=arch_violations,
            match_status=match_status
        )
