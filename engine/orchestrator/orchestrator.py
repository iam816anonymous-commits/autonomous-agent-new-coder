import os
import time
import hashlib
import uuid
from typing import Optional, Dict, Any, List
from engine.store import TaskStore
from engine.state_machine import TaskStateMachine
from engine.models import TaskRecord, TaskState, ActorType
from engine.classifier.classifier import TaskClassifier
from engine.classifier.models import TaskClassification, TaskClassificationStatus
from repository.scan import RepositoryAnalyzer
from repository.models import RepositorySnapshot
from engine.operators.registry import OperatorRegistry
from engine.runtime.sandbox.manager import SandboxManager
from engine.runtime.verifier import VerificationPlanner, VerificationRunner
from .models import (
    OrchestrationState, EngineeringPlan, PlanStepStatus, ExecutionResult, FailureCategory, OrchestrationReport
)
from .planner import EngineeringPlanner
from .plan_validator import PlanValidator
from .dag import PlanDependencyGraph
from .operator_selection import OperatorSelector
from .proposal_pipeline import ProposalPipeline
from .approval import ApprovalPolicy, ApprovalDecision
from .recovery import FailureAnalyzer, ReplanningEngine
from .evidence import OrchestrationEvidenceCollector
from .reporting import OrchestrationReporter
from .errors import OrchestrationError, PlanningError, PlanValidationError, ApprovalRequiredError, RecoveryError

# Phase G Durability Subsystem
from .durability.models import WorkflowExecution, WorkflowStatus, StepExecution, StepStatus
from .durability.store import DurableStore
from .durability.checkpoint import CheckpointManager
from .durability.fingerprints import Fingerprinter
from .durability.events import WorkflowEventLog
from .durability.idempotency import IdempotencyGuard
from .durability.resume import WorkflowResumer
from .durability.replay import WorkflowReplayEngine, ReplayRequest, ReplayMode

class EngineeringOrchestrator:
    """
    Central deterministic orchestrator for Mini-Jules.
    Connects: Repo Analysis -> Classification -> Planning -> Proposal -> Approval -> Sandbox Transaction -> Verification -> Recovery.
    Enforces durable sequence checkpointing, idempotency key checks, and replay isolation.
    Operates 100% offline without LLMs or network access.
    """
    def __init__(
        self,
        store: Optional[TaskStore] = None,
        durable_store: Optional[DurableStore] = None,
        registry: Optional[OperatorRegistry] = None,
        sandbox_manager: Optional[SandboxManager] = None
    ):
        self.store = store or TaskStore()
        self.durable_store = durable_store or DurableStore()
        self.state_machine = TaskStateMachine(self.store)
        self.classifier = TaskClassifier()
        self.planner = EngineeringPlanner(registry)
        self.validator = PlanValidator()
        self.selector = OperatorSelector(registry)
        self.sandbox_manager = sandbox_manager or SandboxManager()
        self.vplanner = VerificationPlanner()
        self.vrunner = VerificationRunner(state_machine=self.state_machine)

        # Durability managers
        self.chk_mgr = CheckpointManager(self.durable_store)
        self.idempotency_guard = IdempotencyGuard(self.durable_store)
        self.resumer = WorkflowResumer(self.durable_store)
        self.replay_engine = WorkflowReplayEngine(self.durable_store)

    def run(
        self,
        repository_root: str,
        request_string: str,
        approved: bool = False,
        explicit_approval: Optional[ApprovalDecision] = None
    ) -> OrchestrationReport:
        real_root = os.path.realpath(repository_root)

        # 1. Create Task Record & Workflow Execution
        record = self.store.create_task(TaskRecord(
            task_id="",
            repository_root=real_root,
            request=request_string,
            status=TaskState.RECEIVED
        ))
        task_id = record.task_id
        collector = OrchestrationEvidenceCollector(task_id)

        workflow_id = f"wf-{task_id}"
        wf = WorkflowExecution(
            workflow_id=workflow_id,
            task_id=task_id,
            orchestration_run_id=f"run-{uuid.uuid4().hex[:6]}",
            plan_id="",
            status=WorkflowStatus.RUNNING
        )
        self.durable_store.create_workflow(wf)

        evt1 = WorkflowEventLog.create_event(workflow_id, 1, "WORKFLOW_STARTED", f"corr-{task_id}", {"request": request_string})
        self.durable_store.append_event(evt1)

        # Initial Checkpoint
        chk1 = self.chk_mgr.create_checkpoint(workflow_id, task_id, WorkflowStatus.RUNNING)

        # 2. Analyze Repository
        self.state_machine.transition(task_id, TaskState.ANALYZING, reason="Analyzing repository structure", actor=ActorType.SYSTEM)
        snapshot = RepositoryAnalyzer.analyze(real_root)
        file_count = len(snapshot.info.source_files) + len(snapshot.info.test_files)
        repo_fingerprint = getattr(snapshot, "summary_hash", hashlib.sha256(snapshot.root.encode("utf-8")).hexdigest()[:12])
        wf.workspace_fingerprint = repo_fingerprint

        # 3. Classify Task
        classification = self.classifier.classify(request_string, snapshot)

        if classification.status != TaskClassificationStatus.SUPPORTED:
            self.state_machine.transition(task_id, TaskState.FAILED, reason="Task classification unsupported or ambiguous", actor=ActorType.SYSTEM)
            self.chk_mgr.create_checkpoint(workflow_id, task_id, WorkflowStatus.FAILED)
            return OrchestrationReporter.generate_report(
                task_id=task_id, request=request_string, classification=classification, repository_summary=snapshot, final_status=OrchestrationState.FAILED
            )

        # 4. Generate & Validate Plan
        self.state_machine.transition(task_id, TaskState.PLANNED, reason="Generating deterministic plan", actor=ActorType.SYSTEM)
        plan = self.planner.create_plan(task_id, classification, snapshot)
        self.validator.validate_plan(plan, real_root)
        plan_fp = Fingerprinter.compute_plan_fingerprint(plan)
        wf.plan_id = plan.plan_id
        wf.plan_fingerprint = plan_fp

        # Checkpoint after planning
        self.chk_mgr.create_checkpoint(
            workflow_id, task_id, WorkflowStatus.RUNNING,
            pending_steps=[s.step_id for s in plan.steps],
            workspace_fingerprint=repo_fingerprint, plan_fingerprint=plan_fp
        )

        # 5. Build Proposal
        dag = PlanDependencyGraph(plan.steps)
        step = dag.get_topological_order()[0]
        op = self.selector.select_operator(step.task_type)
        from engine.operators.context import OperatorContext
        op_ctx = OperatorContext(repository_root=real_root, task_id=task_id, classification=classification, repo_snapshot=snapshot)

        pipeline = ProposalPipeline(op, op_ctx)
        proposal = pipeline.generate_proposal()

        # 6. Approval Gate
        requires_approval = ApprovalPolicy.evaluate_approval_requirement(plan)
        if requires_approval and not approved and explicit_approval is None:
            self.state_machine.transition(task_id, TaskState.AWAITING_APPROVAL, reason="Plan requires human approval", actor=ActorType.SYSTEM)
            self.chk_mgr.create_checkpoint(
                workflow_id, task_id, WorkflowStatus.WAITING_FOR_APPROVAL, current_step=step.step_id,
                workspace_fingerprint=repo_fingerprint, plan_fingerprint=plan_fp
            )
            return OrchestrationReporter.generate_report(
                task_id=task_id, request=request_string, classification=classification, repository_summary=snapshot, plan=plan, final_status=OrchestrationState.AWAITING_APPROVAL
            )

        if explicit_approval is not None:
            valid_appr = ApprovalPolicy.validate_approval(explicit_approval, task_id, plan.plan_id, proposal.transaction_id, repo_fingerprint)
            if not valid_appr:
                raise ApprovalRequiredError("Provided approval is invalid, expired, or fingerprint mismatched.")

        # 7. Idempotency Check & Transactional Execution
        input_fp = Fingerprinter.compute_step_input_fingerprint(workflow_id, step, attempt=1)
        already_completed, existing_step_exec = self.idempotency_guard.check_execution_state(workflow_id, input_fp)

        if not already_completed:
            step_exec = StepExecution(
                step_execution_id=f"step-exec-{uuid.uuid4().hex[:8]}",
                workflow_id=workflow_id,
                step_id=step.step_id,
                operator_name=op.__class__.__name__,
                status=StepStatus.RUNNING,
                proposal_id=proposal.transaction_id,
                transaction_id=proposal.transaction_id,
                attempt_number=1,
                input_fingerprint=input_fp
            )
            self.durable_store.create_step_execution(step_exec)

            self.state_machine.transition(task_id, TaskState.EXECUTING, reason="Executing plan steps in transactional sandbox", actor=ActorType.SYSTEM)
            apply_res = op.apply(op_ctx, proposal, approved=True)

            if not apply_res.success:
                step_exec.status = StepStatus.FAILED
                step_exec.error = apply_res.error
                self.durable_store.update_step_execution(step_exec)
                self.chk_mgr.create_checkpoint(workflow_id, task_id, WorkflowStatus.FAILED, current_step=step.step_id)
                self.state_machine.transition(task_id, TaskState.FAILED, reason=f"Operator apply failed: {apply_res.error}", actor=ActorType.SYSTEM)
                return OrchestrationReporter.generate_report(
                    task_id=task_id, request=request_string, classification=classification, repository_summary=snapshot, plan=plan, final_status=OrchestrationState.FAILED
                )

            step_exec.status = StepStatus.COMPLETED
            step_exec.completed_at = time.time()
            self.durable_store.update_step_execution(step_exec)

        # 8. Verification Pipeline
        self.state_machine.transition(task_id, TaskState.VERIFYING, reason="Running verification suite", actor=ActorType.SYSTEM)
        vplan = self.vplanner.build_plan(task_id, proposal, snapshot)
        vres = self.vrunner.run_verification(context=op_ctx, proposal=proposal, operator=op, plan=vplan, execution_approved=True)

        if vres.status.value in ("PASSED", "COMPLETED"):
            self.state_machine.transition(task_id, TaskState.COMPLETED, reason="All verification checks passed", actor=ActorType.SYSTEM)
            self.chk_mgr.create_checkpoint(
                workflow_id, task_id, WorkflowStatus.COMPLETED, completed_steps=[step.step_id], pending_steps=[]
            )
            exec_result = ExecutionResult(
                execution_id=f"exec-{task_id}", plan_id=plan.plan_id, step_id=step.step_id, transaction_id=proposal.transaction_id,
                status=PlanStepStatus.VERIFIED, proposal_id=proposal.transaction_id, verification_result={"status": vres.status.value}
            )
            return OrchestrationReporter.generate_report(
                task_id=task_id, request=request_string, classification=classification, repository_summary=snapshot, plan=plan, results=[exec_result], final_status=OrchestrationState.COMPLETED
            )
        else:
            self.state_machine.transition(task_id, TaskState.FAILED, reason=f"Verification failed: {vres.summary}", actor=ActorType.SYSTEM)
            self.chk_mgr.create_checkpoint(workflow_id, task_id, WorkflowStatus.FAILED, current_step=step.step_id)
            exec_result = ExecutionResult(
                execution_id=f"exec-{task_id}", plan_id=plan.plan_id, step_id=step.step_id, transaction_id=proposal.transaction_id,
                status=PlanStepStatus.FAILED, proposal_id=proposal.transaction_id, verification_result={"status": vres.status.value}, error=vres.summary
            )
            diag = FailureAnalyzer.diagnose(exec_result)
            return OrchestrationReporter.generate_report(
                task_id=task_id, request=request_string, classification=classification, repository_summary=snapshot, plan=plan, results=[exec_result], diagnoses=[diag], final_status=OrchestrationState.FAILED
            )
