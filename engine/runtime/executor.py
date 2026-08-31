import json
import os
from typing import List, Optional
from dataclasses import asdict
from .models import (
    CommandRequest,
    ExecutionResult,
    ExecutionRiskLevel,
    ExecutionStatus
)
from .command_registry import CommandRegistry
from .policy import RuntimePolicy
from .environment import ExecutionEnvironment, LocalRestrictedEnvironment
from .errors import ExecutionApprovalRequiredError
from engine.artifacts import ArtifactManager

class CommandExecutor:
    """
    Executes predefined verification commands inside a controlled environment.
    Enforces risk-based execution approval boundaries and persists execution logs.
    """
    def __init__(
        self,
        registry: Optional[CommandRegistry] = None,
        policy: Optional[RuntimePolicy] = None,
        environment: Optional[ExecutionEnvironment] = None,
        artifact_manager: Optional[ArtifactManager] = None
    ):
        self.policy = policy or RuntimePolicy()
        self.registry = registry or CommandRegistry(self.policy)
        self.environment = environment or LocalRestrictedEnvironment(self.policy)
        self.artifact_manager = artifact_manager or ArtifactManager()

    def execute(
        self,
        request: CommandRequest,
        repo_root: str,
        task_id: str,
        execution_approved: bool = False
    ) -> ExecutionResult:
        cmd_def = self.registry.get(request.command_name)

        # High-risk execution approval check
        if cmd_def.risk_level == ExecutionRiskLevel.HIGH and self.policy.require_approval_for_high_risk:
            if not execution_approved:
                raise ExecutionApprovalRequiredError(
                    f"Execution approval boundary rejected: command '{cmd_def.name}' has risk HIGH "
                    f"(executes project code) and requires explicit execution_approved=True."
                )

        work_dir = request.working_directory or "."
        res = self.environment.execute_command(
            command_def=cmd_def,
            extra_arguments=request.extra_arguments,
            working_directory=work_dir,
            repo_root=repo_root
        )

        # Persist execution artifacts
        try:
            artifact_filename = f"{res.execution_id}_result.json"
            self.artifact_manager.write_artifact(task_id, artifact_filename, json.dumps(asdict(res), indent=2))
        except Exception:
            pass # Non-fatal artifact persistence fallback

        return res
