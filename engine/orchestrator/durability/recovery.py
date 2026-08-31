from typing import List, Dict, Any, Optional
from .models import WorkflowExecution, WorkflowStatus, Checkpoint
from .store import DurableStore
from .errors import RecoveryError

class WorkflowRecoveryManager:
    """
    Identifies interrupted workflows following process crashes and determines safe resume vs fail-closed outcomes.
    """
    def __init__(self, store: Optional[DurableStore] = None):
        self.store = store or DurableStore()

    def inspect_recovery_safety(self, workflow_id: str, current_workspace_fingerprint: str) -> Dict[str, Any]:
        wf = self.store.get_workflow(workflow_id)
        if not wf:
            raise RecoveryError(f"Workflow '{workflow_id}' not found.")

        latest_chk = self.store.get_latest_checkpoint(workflow_id)
        if not latest_chk:
            return {
                "safe_to_resume": False,
                "reason": "NO_CHECKPOINT_FOUND",
                "recommended_status": WorkflowStatus.FAILED
            }

        # Check workspace consistency
        if latest_chk.workspace_fingerprint and current_workspace_fingerprint:
            if latest_chk.workspace_fingerprint != current_workspace_fingerprint:
                return {
                    "safe_to_resume": False,
                    "reason": "WORKSPACE_FINGERPRINT_MISMATCH",
                    "recommended_status": WorkflowStatus.RECOVERY_REQUIRED
                }

        # If crashed during approval or waiting
        if latest_chk.workflow_status in (WorkflowStatus.WAITING_FOR_APPROVAL, WorkflowStatus.PAUSED):
            return {
                "safe_to_resume": True,
                "reason": "AWAITING_APPROVAL_SAFE",
                "recommended_status": latest_chk.workflow_status,
                "checkpoint": latest_chk
            }

        # If crashed during RUNNING state
        if wf.status == WorkflowStatus.RUNNING:
            return {
                "safe_to_resume": True,
                "reason": "RESUME_FROM_LAST_CHECKPOINT",
                "recommended_status": WorkflowStatus.RUNNING,
                "checkpoint": latest_chk
            }

        return {
            "safe_to_resume": False,
            "reason": f"WORKFLOW_STATUS_{wf.status.value}",
            "recommended_status": wf.status,
            "checkpoint": latest_chk
        }
