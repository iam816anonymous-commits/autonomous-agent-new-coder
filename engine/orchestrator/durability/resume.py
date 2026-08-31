from typing import Dict, Any, Optional
from .models import WorkflowExecution, WorkflowStatus, Checkpoint
from .store import DurableStore
from .recovery import WorkflowRecoveryManager
from .errors import RecoveryError

class WorkflowResumer:
    """
    Restores execution context and determines next step boundary for interrupted workflows.
    """
    def __init__(self, store: Optional[DurableStore] = None):
        self.store = store or DurableStore()
        self.recovery_mgr = WorkflowRecoveryManager(self.store)

    def resume_workflow(self, workflow_id: str, current_workspace_fingerprint: str) -> Dict[str, Any]:
        safety = self.recovery_mgr.inspect_recovery_safety(workflow_id, current_workspace_fingerprint)
        if not safety.get("safe_to_resume", False):
            raise RecoveryError(f"Workflow '{workflow_id}' cannot be safely resumed: {safety.get('reason')}")

        chk: Checkpoint = safety["checkpoint"]
        next_step = chk.pending_steps[0] if chk.pending_steps else None

        return {
            "workflow_id": workflow_id,
            "task_id": chk.task_id,
            "resumed_from_checkpoint": chk.checkpoint_id,
            "completed_steps": chk.completed_steps,
            "next_step": next_step,
            "execution_state": chk.execution_state
        }
