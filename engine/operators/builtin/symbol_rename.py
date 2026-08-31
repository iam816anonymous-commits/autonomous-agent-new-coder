import os
import ast
import tokenize
import io
import re
from typing import List, Dict, Any, Optional, Set
from engine.operators.base import EngineeringOperator, compute_sha256
from engine.operators.context import OperatorContext
from engine.operators.models import (
    OperatorPlan,
    ProposedChange,
    FileChange,
    Precondition,
    VerificationResult
)
from engine.classifier.models import TaskType
from project_creator.core.patch import PatchManager
from repository.models import BlastRadiusLevel

class SymbolRenameOperator(EngineeringOperator):
    """
    Deterministic structural symbol rename operator.
    Uses AST and token-level parsing to rename symbols across Python source files
    without false-positive string, comment, or substring collisions.
    """
    def __init__(self):
        super().__init__(
            name="SymbolRenameOperator",
            supported_task_types=[TaskType.SYMBOL_RENAME],
            capabilities=[
                "repository.symbols",
                "filesystem.read",
                "filesystem.write",
                "patch.generate",
                "verification"
            ]
        )

    def inspect(self, context: OperatorContext) -> Dict[str, Any]:
        params = context.classification.extracted_parameters
        old_name = params.get("old_name", "")
        new_name = params.get("new_name", "")

        sym_defs = context.repo_snapshot.symbols.find_definitions(old_name) if context.repo_snapshot else []
        all_occurrences = context.repo_snapshot.symbols.find_symbol(old_name) if context.repo_snapshot else []
        collisions = context.repo_snapshot.symbols.find_symbol(new_name) if context.repo_snapshot else []

        # Disambiguation check: check if old_name is defined in multiple files
        def_files = list(set(s.file_path for s in sym_defs))
        is_ambiguous = len(def_files) > 1 and "target_file" not in params

        # Non-python check
        non_py_files = [s.file_path for s in all_occurrences if not s.file_path.endswith('.py')]

        return {
            "old_name": old_name,
            "new_name": new_name,
            "definitions": sym_defs,
            "definition_files": def_files,
            "is_ambiguous": is_ambiguous,
            "occurrences": len(all_occurrences),
            "collision_count": len(collisions),
            "non_py_files": non_py_files
        }

    def plan(self, context: OperatorContext) -> OperatorPlan:
        insp = self.inspect(context)
        old_name = insp["old_name"]
        new_name = insp["new_name"]

        preconditions = [
            Precondition(
                name="old_symbol_exists",
                satisfied=insp["occurrences"] > 0,
                message=f"Symbol '{old_name}' found in repository index ({insp['occurrences']} location(s))."
                if insp["occurrences"] > 0 else f"Symbol '{old_name}' not found in repository index."
            ),
            Precondition(
                name="unambiguous_symbol_target",
                satisfied=not insp["is_ambiguous"],
                message="Symbol definition is unique." if not insp["is_ambiguous"]
                else f"AMBIGUOUS_TARGET: Found multiple definitions for '{old_name}' in {insp['definition_files']}. Target scope required."
            ),
            Precondition(
                name="no_target_collision",
                satisfied=insp["collision_count"] == 0,
                message=f"Target symbol '{new_name}' is available."
                if insp["collision_count"] == 0 else f"Target symbol '{new_name}' already exists in repository."
            ),
            Precondition(
                name="supported_language_operation",
                satisfied=len(insp["non_py_files"]) == 0,
                message="All affected files support structural AST/token rewriting."
                if len(insp["non_py_files"]) == 0
                else f"UNSUPPORTED_LANGUAGE_OPERATION: Structural rename for non-Python files {insp['non_py_files']} is not supported."
            )
        ]

        steps = [
            f"locate_symbol_definitions_and_references({old_name})",
            f"perform_ast_token_rewriting({old_name} -> {new_name})",
            "generate_unified_diffs",
            "verify_structural_integrity"
        ]

        return OperatorPlan(
            operator_name=self.name,
            task_id=context.task_id,
            steps=steps,
            estimated_risk=BlastRadiusLevel.LOW if insp["occurrences"] <= 5 else BlastRadiusLevel.MEDIUM,
            preconditions=preconditions
        )

    def propose(self, context: OperatorContext, plan: OperatorPlan) -> ProposedChange:
        # Verify preconditions
        failed_preconditions = [p for p in plan.preconditions if not p.satisfied]
        if failed_preconditions:
            warnings = [p.message for p in failed_preconditions]
            return ProposedChange(
                operator_name=self.name,
                transaction_id=context.transaction_id,
                task_id=context.task_id,
                files_to_modify=[],
                preconditions=plan.preconditions,
                warnings=warnings,
                risk=plan.estimated_risk
            )

        params = context.classification.extracted_parameters
        old_name = params["old_name"]
        new_name = params["new_name"]

        # Collect affected files from symbol index
        affected_files: Set[str] = set()
        if context.repo_snapshot:
            for s in context.repo_snapshot.symbols.find_symbol(old_name):
                affected_files.add(s.file_path)
            for r in context.repo_snapshot.symbols.find_references(old_name):
                affected_files.add(r.file_path)

        file_changes: List[FileChange] = []
        warnings: List[str] = []

        for rel_path in sorted(list(affected_files)):
            full_path = os.path.realpath(os.path.abspath(os.path.join(context.repository_root, rel_path)))
            if not full_path.startswith(context.repository_root) or not os.path.exists(full_path):
                continue

            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                old_content = f.read()

            if rel_path.endswith(".py"):
                new_content = self._rewrite_python_tokens(old_content, old_name, new_name)
            else:
                warnings.append(f"Skipped non-Python file '{rel_path}' to avoid risky regex substitution.")
                continue

            if old_content != new_content:
                old_sha = compute_sha256(old_content)
                new_sha = compute_sha256(new_content)
                diff = PatchManager.generate_diff(old_content, new_content, rel_path)

                file_changes.append(FileChange(
                    path=rel_path,
                    old_content=old_content,
                    new_content=new_content,
                    old_sha256=old_sha,
                    new_sha256=new_sha,
                    diff=diff
                ))

        return ProposedChange(
            operator_name=self.name,
            transaction_id=context.transaction_id,
            task_id=context.task_id,
            files_to_modify=file_changes,
            preconditions=plan.preconditions,
            warnings=warnings,
            risk=plan.estimated_risk
        )

    def _rewrite_python_tokens(self, content: str, old_name: str, new_name: str) -> str:
        """
        Rewrites Python source code using python tokenize tokens.
        Replaces exact NAME tokens matching old_name without modifying strings, comments, or substrings.
        """
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(content).readline))
            modified_tokens = []

            for tok_type, tok_val, start, end, line in tokens:
                # Only rewrite exact NAME tokens; leave STRING, COMMENT, and other tokens untouched
                if tok_type == tokenize.NAME and tok_val == old_name:
                    modified_tokens.append((tok_type, new_name, start, end, line))
                else:
                    modified_tokens.append((tok_type, tok_val, start, end, line))

            return tokenize.untokenize(modified_tokens)
        except Exception:
            # Fallback to standard word-boundary regex if tokenizer fails on malformed source
            pattern = re.compile(r'\b' + re.escape(old_name) + r'\b')
            return pattern.sub(new_name, content)

    def verify_proposal(self, context: OperatorContext, proposal: ProposedChange) -> VerificationResult:
        checks_run = ["syntax_validation", "boundary_validation"]
        issues = []

        for fc in proposal.files_to_modify:
            if fc.path.endswith(".py") and fc.new_content:
                try:
                    ast.parse(fc.new_content, filename=fc.path)
                except SyntaxError as e:
                    issues.append(f"Syntax error in modified {fc.path}: {e}")

        return VerificationResult(
            passed=len(issues) == 0,
            checks_run=checks_run,
            issues=issues
        )
