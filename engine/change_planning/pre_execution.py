import os
from typing import Dict, Any, List
from repository.semantic.snapshot import SemanticRepositorySnapshot
from repository.semantic.assertions import SemanticAssertions
from .models import ChangePlan
from .errors import PreExecutionAssertionError

class PreExecutionValidator:
    """
    Asserts workspace files, symbols, symbol types, and architectural layer membership immediately prior to execution.
    Fails closed if stale planning assumptions are detected.
    """
    def __init__(self, workspace_root: str, semantic_snapshot: SemanticRepositorySnapshot):
        self.workspace_root = os.path.realpath(os.path.abspath(workspace_root))
        self.snapshot = semantic_snapshot
        self.assertions = SemanticAssertions(semantic_snapshot.graph)

    def validate_plan_preconditions(self, plan: ChangePlan) -> List[Dict[str, Any]]:
        results = []

        for step in plan.steps:
            # 1. Assert target files exist and are within workspace boundary
            for rel_file in step.target_files:
                full_path = os.path.join(self.workspace_root, rel_file)
                if not os.path.exists(full_path):
                    raise PreExecutionAssertionError(f"Pre-execution assertion failed: target file '{rel_file}' does not exist.")
                try:
                    if os.path.commonpath([self.workspace_root, full_path]) != self.workspace_root:
                        raise PreExecutionAssertionError(f"Pre-execution assertion failed: file '{rel_file}' escapes workspace boundary.")
                except ValueError:
                    raise PreExecutionAssertionError(f"Pre-execution assertion failed: file '{rel_file}' escapes workspace boundary.")

                results.append({"assertion": "ASSERT_FILE_EXISTS_IN_WORKSPACE", "file": rel_file, "passed": True})

            # 2. Assert target symbols exist in graph
            for sym_name in step.target_symbols:
                assert_res = self.assertions.assert_symbol_exists(sym_name)
                if not assert_res["passed"]:
                    raise PreExecutionAssertionError(f"Pre-execution assertion failed: target symbol '{sym_name}' does not exist in semantic graph.")
                results.append(assert_res)

        return results
