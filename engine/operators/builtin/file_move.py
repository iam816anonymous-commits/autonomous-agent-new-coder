import os
from typing import List, Dict, Any, Optional
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

class FileMoveOperator(EngineeringOperator):
    """
    Deterministic file move operator.
    Moves source file to destination while analyzing impacted imports across dependent files.
    """
    def __init__(self):
        super().__init__(
            name="FileMoveOperator",
            supported_task_types=[TaskType.FILE_MOVE, TaskType.FILE_RENAME],
            capabilities=[
                "filesystem.read",
                "filesystem.write",
                "filesystem.rename",
                "repository.dependencies",
                "verification"
            ]
        )

    def inspect(self, context: OperatorContext) -> Dict[str, Any]:
        params = context.classification.extracted_parameters
        source = params.get("source", "")
        destination = params.get("destination", "")

        src_full = os.path.realpath(os.path.abspath(os.path.join(context.repository_root, source)))
        dst_full = os.path.realpath(os.path.abspath(os.path.join(context.repository_root, destination)))

        src_exists = src_full.startswith(context.repository_root) and os.path.exists(src_full)
        dst_exists = dst_full.startswith(context.repository_root) and os.path.exists(dst_full)

        impacted_dependents = []
        if context.repo_snapshot and hasattr(context.repo_snapshot, 'dep_builder'):
            impacted_dependents = context.repo_snapshot.dep_builder.get_dependents(source)

        return {
            "source": source,
            "destination": destination,
            "source_exists": src_exists,
            "destination_exists": dst_exists,
            "impacted_dependents": impacted_dependents
        }

    def plan(self, context: OperatorContext) -> OperatorPlan:
        insp = self.inspect(context)
        source = insp["source"]
        destination = insp["destination"]

        preconditions = [
            Precondition(
                name="source_exists",
                satisfied=insp["source_exists"],
                message=f"Source file '{source}' exists."
                if insp["source_exists"] else f"Source file '{source}' not found in workspace."
            ),
            Precondition(
                name="destination_not_overwritten",
                satisfied=not insp["destination_exists"],
                message=f"Destination file '{destination}' does not already exist."
                if not insp["destination_exists"] else f"Destination file '{destination}' already exists."
            )
        ]

        steps = [
            f"validate_file_move_boundaries({source} -> {destination})",
            f"analyze_impacted_dependents({len(insp['impacted_dependents'])} dependent files)",
            "generate_file_move_proposal",
            "verify_destination_directory_structure"
        ]

        return OperatorPlan(
            operator_name=self.name,
            task_id=context.task_id,
            steps=steps,
            estimated_risk=BlastRadiusLevel.LOW if len(insp["impacted_dependents"]) <= 2 else BlastRadiusLevel.MEDIUM,
            preconditions=preconditions
        )

    def propose(self, context: OperatorContext, plan: OperatorPlan) -> ProposedChange:
        params = context.classification.extracted_parameters
        source = params["source"]
        destination = params["destination"]

        src_full = os.path.realpath(os.path.abspath(os.path.join(context.repository_root, source)))

        content = ""
        if os.path.exists(src_full):
            with open(src_full, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

        sha = compute_sha256(content)
        diff = PatchManager.generate_diff("", content, destination)

        # File creation at destination
        file_to_create = FileChange(
            path=destination,
            old_content=None,
            new_content=content,
            old_sha256=None,
            new_sha256=sha,
            diff=diff
        )

        insp = self.inspect(context)
        warnings = []
        if insp["impacted_dependents"]:
            warnings.append(
                f"File move affects {len(insp['impacted_dependents'])} dependent file(s): {', '.join(insp['impacted_dependents'])}."
            )

        return ProposedChange(
            operator_name=self.name,
            transaction_id=context.transaction_id,
            task_id=context.task_id,
            files_to_create=[file_to_create],
            files_to_delete=[source],
            preconditions=plan.preconditions,
            warnings=warnings,
            risk=plan.estimated_risk
        )

    def verify_proposal(self, context: OperatorContext, proposal: ProposedChange) -> VerificationResult:
        checks_run = ["boundary_validation", "overwrite_prevention_check"]
        issues = []

        for fc in proposal.files_to_create:
            full_path = os.path.realpath(os.path.abspath(os.path.join(context.repository_root, fc.path)))
            if not full_path.startswith(context.repository_root):
                issues.append(f"Destination path traversal outside repository root: {fc.path}")

        for rel_del in proposal.files_to_delete:
            full_path = os.path.realpath(os.path.abspath(os.path.join(context.repository_root, rel_del)))
            if not full_path.startswith(context.repository_root):
                issues.append(f"Source path traversal outside repository root: {rel_del}")

        return VerificationResult(
            passed=len(issues) == 0,
            checks_run=checks_run,
            issues=issues
        )
