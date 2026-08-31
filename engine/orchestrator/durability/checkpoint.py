import time
import uuid
from typing import Dict, Any, List, Optional
from .models import Checkpoint, WorkflowStatus, WorkflowExecution
from .store import DurableStore
from .errors import CheckpointError

class CheckpointManager:
    """
    Manages sequence-ordered, immutable checkpoint creation, retrieval, and consistency validation.
    """
    def __init__(self, store: Optional[DurableStore] = None):
        self.store = store or DurableStore()

    def create_checkpoint(
        self,
        workflow_id: str,
        task_id: str,
        workflow_status: WorkflowStatus,
        current_step: Optional[str] = None,
        completed_steps: Optional[List[str]] = None,
        pending_steps: Optional[List[str]] = None,
        workspace_fingerprint: str = "",
        plan_fingerprint: str = "",
        execution_state: Optional[Dict[str, Any]] = None
    ) -> Checkpoint:
        latest = self.store.get_latest_checkpoint(workflow_id)
        next_seq = (latest.sequence_number + 1) if latest else 1
        prev_id = latest.checkpoint_id if latest else None

        chk_id = f"chk-{workflow_id}-{next_seq}-{uuid.uuid4().hex[:6]}"
        chk = Checkpoint(
            checkpoint_id=chk_id,
            workflow_id=workflow_id,
            task_id=task_id,
            sequence_number=next_seq,
            timestamp=time.time(),
            workflow_status=workflow_status,
            current_step=current_step,
            completed_steps=completed_steps or [],
            pending_steps=pending_steps or [],
            workspace_fingerprint=workspace_fingerprint,
            plan_fingerprint=plan_fingerprint,
            execution_state=execution_state or {},
            previous_checkpoint_id=prev_id
        )

        return self.store.create_checkpoint(chk)

    def get_latest_checkpoint(self, workflow_id: str) -> Optional[Checkpoint]:
        return self.store.get_latest_checkpoint(workflow_id)

    def validate_checkpoint_consistency(self, chk: Checkpoint, expected_workspace_hash: str) -> bool:
        if not chk:
            return False
        if chk.workspace_fingerprint and expected_workspace_hash:
            if chk.workspace_fingerprint != expected_workspace_hash:
                return False
        return True
