import uuid
import time
import hashlib
from typing import Optional, Dict, Any, List, Set
from engine.classifier.models import TaskClassification, TaskClassificationStatus, TaskType
from repository.scan import RepositorySnapshot
from repository.impact_analysis import ImpactAnalyzer
from repository.semantic.snapshot import SemanticSnapshotter
from repository.semantic.resolver import SemanticResolver
from repository.semantic.trust.trust_levels import SemanticTrustEvaluator
from repository.semantic.trust.models import SemanticTrustLevel
from engine.operators.registry import OperatorRegistry
from engine.runtime.sandbox.models import ExecutionCapability
from .models import EngineeringPlan, EngineeringPlanStep, PlanStepStatus
from .errors import PlanningError
from .operator_selection import OperatorSelector

class EngineeringPlanner:
    """
    Deterministically generates EngineeringPlan objects incorporating semantic trust evaluation.
    Enforces REQUIRES_DISCOVERY when planning confidence or trust level is insufficient.
    """
    def __init__(self, registry: Optional[OperatorRegistry] = None):
        self.selector = OperatorSelector(registry)

    def create_plan(
        self,
        task_id: str,
        classification: TaskClassification,
        repo_snapshot: RepositorySnapshot
    ) -> EngineeringPlan:
        # 1. Fail closed on unsupported or ambiguous classification
        if classification.status != TaskClassificationStatus.SUPPORTED:
            raise PlanningError(f"Cannot generate plan: task status is '{classification.status.value}' (reason: {classification.extracted_parameters.get('reason')}).")

        # 2. Semantic Analysis & Trust Gate
        semantic_snap = SemanticSnapshotter.capture(repo_snapshot)
        resolver = SemanticResolver(semantic_snap.graph)

        if classification.task_type == TaskType.SYMBOL_RENAME:
            old_name = classification.extracted_parameters.get("old_name", "")
            res = resolver.resolve_definition(old_name)
            if res["status"] == "AMBIGUOUS":
                raise PlanningError(f"REQUIRES_DISCOVERY: Symbol '{old_name}' is ambiguous ({len(res['matches'])} matches found).")
            elif res["status"] == "UNRESOLVED":
                raise PlanningError(f"Planning failed: Symbol '{old_name}' does not exist in repository.")

            # Evaluate Trust Level
            symbol = res["symbol"]
            trust_res = SemanticTrustEvaluator.evaluate_symbol_trust(symbol)
            if trust_res.trust_level in (SemanticTrustLevel.LOW_CONFIDENCE, SemanticTrustLevel.UNKNOWN, SemanticTrustLevel.UNTRUSTED):
                raise PlanningError(f"REQUIRES_DISCOVERY: Symbol '{old_name}' has insufficient trust level '{trust_res.trust_level.value}'.")

        # 3. Match operator via OperatorSelector
        op = self.selector.select_operator(classification.task_type, repo_snapshot)
        op_name = op.__class__.__name__

        # 4. Impact Analysis
        target_files = []
        if classification.task_type == TaskType.SYMBOL_RENAME:
            old_name = classification.extracted_parameters.get("old_name", "")
            matches = [s for s in repo_snapshot.symbols.symbols if s.name == old_name]
            target_files = sorted(list(set([s.file_path for s in matches])))
        elif classification.task_type == TaskType.FILE_MOVE:
            src = classification.extracted_parameters.get("source") or classification.extracted_parameters.get("source_path", "")
            target_files = [src] if src else []

        impact = ImpactAnalyzer.analyze_impact(repo_snapshot, target_files)
        blast_radius = impact.blast_radius.value

        # 5. Required Capabilities
        required_caps: Set[ExecutionCapability] = {ExecutionCapability.STATIC_ANALYSIS, ExecutionCapability.READ_WORKSPACE}
        if classification.task_type in (TaskType.SYMBOL_RENAME, TaskType.FILE_MOVE):
            required_caps.add(ExecutionCapability.WRITE_WORKSPACE)
            required_caps.add(ExecutionCapability.EXECUTE_COMMAND)

        # 6. Build Step
        step_id = f"step-{uuid.uuid4().hex[:8]}"
        step = EngineeringPlanStep(
            step_id=step_id,
            order=1,
            task_type=classification.task_type,
            operator_name=op_name,
            parameters=classification.extracted_parameters,
            dependencies=[],
            affected_files=impact.affected_files,
            affected_symbols=impact.affected_symbols,
            expected_changes=[f"Apply {classification.task_type.value} using {op_name}"],
            verification_profile="PYTHON_SYNTAX_ONLY",
            risk_level=impact.blast_radius.value,
            status=PlanStepStatus.PENDING
        )

        plan_id = f"plan-{uuid.uuid4().hex[:8]}"
        approval_required = blast_radius in ("MEDIUM", "HIGH", "CRITICAL")
        repo_fingerprint = getattr(repo_snapshot, "summary_hash", hashlib.sha256(repo_snapshot.root.encode("utf-8")).hexdigest()[:12])

        return EngineeringPlan(
            plan_id=plan_id,
            task_id=task_id,
            repository_fingerprint=repo_fingerprint,
            task_classification=classification,
            steps=[step],
            risk_level=blast_radius,
            estimated_blast_radius=blast_radius,
            required_capabilities=required_caps,
            approval_required=approval_required,
            created_at=time.time()
        )
