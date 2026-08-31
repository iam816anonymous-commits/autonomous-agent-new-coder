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
    CommandCategory,
    ExecutionRiskLevel,
    CommandRequest,
    ExecutionStatus
)
from .executor import CommandExecutor
from engine.operators.base import EngineeringOperator
from engine.operators.context import OperatorContext
from engine.operators.models import ProposedChange
from engine.state_machine import TaskStateMachine
from engine.models import TaskState, ActorType

class VerificationPlanner:
    """
    Constructs deterministic verification plans based on proposed changes and Phase A impact analysis.
    """
    def build_plan(
        self,
        task_id: str,
        proposal: ProposedChange,
        repo_snapshot=None
    ) -> VerificationPlan:
        plan_id = f"VPLAN-{uuid.uuid4().hex[:8]}"
        steps: List[VerificationStep] = []

        # 1. Syntax Check Step
        steps.append(VerificationStep(
            step_id="step_1_syntax",
            command_name="python_syntax_check",
            category=CommandCategory.SYNTAX_CHECK,
            required=True,
            risk_level=ExecutionRiskLevel.LOW,
            description="Static Python syntax compilation check"
        ))

        # 2. Targeted Test Step (derived from Phase A impact analysis)
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
                description=f"Targeted pytest for affected files: {', '.join(targeted_tests)}",
                extra_arguments=targeted_tests
            ))

        return VerificationPlan(
            plan_id=plan_id,
            task_id=task_id,
            steps=steps,
            estimated_duration=sum(30.0 for _ in steps)
        )

class VerificationRunner:
    """
    Executes verification plans, updates state machine heartbeats, and triggers operator rollbacks on failure.
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
        execution_approved: bool = False
    ) -> VerificationResultModel:
        ver_id = f"VER-{uuid.uuid4().hex[:8]}"
        step_results = []
        rollback_needed = False

        # Transition task state machine to VERIFYING
        try:
            self.state_machine.transition(
                task_id=context.task_id,
                target_state=TaskState.VERIFYING,
                reason="Starting controlled verification plan execution",
                actor=ActorType.SYSTEM
            )
        except Exception:
            pass # Continue verification if state transition is non-fatal in tests

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
                    rollback_needed = True
                    break

            except Exception as e:
                rollback_needed = True
                break

        if rollback_needed:
            # Trigger targeted operator rollback
            rollback_success = operator.rollback(context, proposal)
            try:
                self.state_machine.transition(
                    task_id=context.task_id,
                    target_state=TaskState.ROLLED_BACK,
                    reason="Verification failed; operator transaction rolled back.",
                    actor=ActorType.SYSTEM
                )
            except Exception:
                pass

            return VerificationResultModel(
                verification_id=ver_id,
                task_id=context.task_id,
                status=VerificationStatus.ROLLED_BACK if rollback_success else VerificationStatus.FAILED,
                step_results=step_results,
                rollback_executed=rollback_success,
                summary="Verification failed. Operator-owned file changes were rolled back."
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
            step_results=step_results,
            rollback_executed=False,
            summary="All verification steps passed successfully."
        )
