import os
import uuid
import json
from typing import List, Dict, Any, Optional
from dataclasses import asdict
from .models import (
    VerificationPlan,
    VerificationStep,
    VerificationResultModel,
    VerificationStatus,
    VerificationLevel,
    CommandCategory,
    ExecutionRiskLevel,
    CommandRequest,
    ExecutionStatus
)
from .executor import CommandExecutor
from .profiles import DEFAULT_PROFILES, get_profile
from .environment import compute_workspace_snapshot_hash
from engine.operators.base import EngineeringOperator
from engine.operators.context import OperatorContext
from engine.operators.models import ProposedChange
from engine.state_machine import TaskStateMachine
from engine.models import TaskState, ActorType

class VerificationPlanner:
    """
    Constructs deterministic verification plans based on verification profiles, proposed changes,
    and Phase A impact analysis.
    """
    def build_plan(
        self,
        task_id: str,
        proposal: ProposedChange,
        repo_snapshot=None,
        profile_id: str = "PYTHON_UNIT_TESTS"
    ) -> VerificationPlan:
        plan_id = f"VPLAN-{uuid.uuid4().hex[:8]}"
        profile = get_profile(profile_id) or DEFAULT_PROFILES["PYTHON_UNIT_TESTS"]
        steps: List[VerificationStep] = []

        # 1. Syntax Check Step
        if CommandCategory.SYNTAX_CHECK in profile.categories:
            steps.append(VerificationStep(
                step_id="step_1_syntax",
                command_name="python_syntax_check",
                category=CommandCategory.SYNTAX_CHECK,
                required=True,
                risk_level=ExecutionRiskLevel.LOW,
                description="Static Python syntax compilation check"
            ))

        # 2. Targeted Test Step (derived from Phase A impact analysis)
        if CommandCategory.TARGETED_TEST in profile.categories:
            targeted_tests = []
            if repo_snapshot:
                for fc in proposal.files_to_modify + proposal.files_to_create:
                    impact = repo_snapshot.analyze_file_impact(fc.path)
                    for t in impact.related_tests:
                        if t not in targeted_tests:
                            targeted_tests.append(t)

            if targeted_tests:
                steps.append(VerificationStep(
                    step_id="step_2_targeted_tests",
                    command_name="pytest_targeted",
                    category=CommandCategory.TARGETED_TEST,
                    required=True,
                    risk_level=ExecutionRiskLevel.HIGH,
                    description=f"Targeted pytest for affected files: [{', '.join(targeted_tests)}]",
                    extra_arguments=targeted_tests
                ))

        # 3. Optional Lint Step
        if CommandCategory.LINT in profile.categories:
            steps.append(VerificationStep(
                step_id="step_3_lint",
                command_name="ruff_lint",
                category=CommandCategory.LINT,
                required=False,
                risk_level=ExecutionRiskLevel.MEDIUM,
                description="Read-only Ruff linter check"
            ))

        return VerificationPlan(
            plan_id=plan_id,
            task_id=task_id,
            steps=steps,
            estimated_duration=sum(30.0 for _ in steps),
            level=profile.default_level
        )

class VerificationRunner:
    """
    Executes verification plans, checks workspace snapshot identity, updates state machine heartbeats,
    and preserves failure evidence artifacts.
    """
    def __init__(
        self,
        executor: Optional[CommandExecutor] = None,
        state_machine: Optional[TaskStateMachine] = None
    ):
        self.executor = executor or CommandExecutor()
        self.state_machine = state_machine or TaskStateMachine()

    def run_verification(
        self,
        context: OperatorContext,
        proposal: ProposedChange,
        operator: EngineeringOperator,
        plan: VerificationPlan,
        execution_approved: bool = False,
        auto_rollback_on_failure: bool = False
    ) -> VerificationResultModel:
        ver_id = f"VER-{uuid.uuid4().hex[:8]}"
        step_results = []
        has_failure = False

        snapshot_start = compute_workspace_snapshot_hash(context.repository_root)

        # Transition task state machine to VERIFYING
        try:
            self.state_machine.transition(
                task_id=context.task_id,
                target_state=TaskState.VERIFYING,
                reason="Starting controlled verification plan execution",
                actor=ActorType.SYSTEM
            )
        except Exception:
            pass

        for step in plan.steps:
            # Heartbeat lease update
            self.state_machine.heartbeat(context.task_id, worker_id="verification_runner")

            request = CommandRequest(
                command_name=step.command_name,
                extra_arguments=step.extra_arguments,
                working_directory="."
            )

            try:
                res = self.executor.execute(
                    request=request,
                    repo_root=context.repository_root,
                    task_id=context.task_id,
                    execution_approved=execution_approved
                )
                step_results.append(res)

                if res.status != ExecutionStatus.PASSED and step.required:
                    has_failure = True
                    break

            except Exception as e:
                has_failure = True
                break

        snapshot_end = compute_workspace_snapshot_hash(context.repository_root)
        if snapshot_start != snapshot_end:
            return VerificationResultModel(
                verification_id=ver_id,
                task_id=context.task_id,
                status=VerificationStatus.WORKSPACE_CHANGED_DURING_VERIFICATION,
                level=plan.level,
                step_results=step_results,
                rollback_executed=False,
                summary="Verification rejected: Workspace state changed unexpectedly during verification execution."
            )

        if has_failure:
            rollback_executed = False
            if auto_rollback_on_failure:
                rollback_executed = operator.rollback(context, proposal)
                try:
                    self.state_machine.transition(
                        task_id=context.task_id,
                        target_state=TaskState.ROLLED_BACK,
                        reason="Verification failed; auto-rollback executed.",
                        actor=ActorType.SYSTEM
                    )
                except Exception:
                    pass

            return VerificationResultModel(
                verification_id=ver_id,
                task_id=context.task_id,
                status=VerificationStatus.ROLLED_BACK if rollback_executed else VerificationStatus.APPLIED_BUT_VERIFICATION_FAILED,
                level=plan.level,
                step_results=step_results,
                rollback_executed=rollback_executed,
                summary="Verification failed. Failure evidence artifacts preserved under task_artifacts/."
            )

        # All required steps passed
        try:
            self.state_machine.transition(
                task_id=context.task_id,
                target_state=TaskState.READY_TO_APPLY,
                reason="All verification steps passed successfully.",
                actor=ActorType.SYSTEM
            )
        except Exception:
            pass

        return VerificationResultModel(
            verification_id=ver_id,
            task_id=context.task_id,
            status=VerificationStatus.PASSED,
            level=plan.level,
            step_results=step_results,
            rollback_executed=False,
            summary="All verification steps passed successfully."
        )
