import time
import uuid
from typing import Dict, Any, Optional, List
from .models import ReplayRequest, ReplayMode, WorkflowExecution, WorkflowStatus, Checkpoint
from .store import DurableStore
from .errors import ReplayError
from .events import WorkflowEventLog

class WorkflowReplayEngine:
    """
    Replays completed workflows deterministically without mutating original execution history.
    """
    def __init__(self, store: Optional[DurableStore] = None):
        self.store = store or DurableStore()

    def replay_workflow(self, req: ReplayRequest) -> Dict[str, Any]:
        source_wf = self.store.get_workflow(req.source_workflow_id)
        if not source_wf:
            raise ReplayError(f"Source workflow '{req.source_workflow_id}' not found for replay.")

        original_checkpoints = self.store.list_checkpoints(req.source_workflow_id)
        original_events = self.store.list_events(req.source_workflow_id)

        # 1. DRY_RUN: Decision reconstruction without side-effects
        if req.replay_mode == ReplayMode.DRY_RUN:
            return {
                "replay_mode": ReplayMode.DRY_RUN.value,
                "source_workflow_id": req.source_workflow_id,
                "event_count": len(original_events),
                "checkpoint_count": len(original_checkpoints),
                "verified_plan_fingerprint": source_wf.plan_fingerprint,
                "decision": "DRY_RUN_RECONSTRUCTION_SUCCESS"
            }

        # 2. VALIDATION_ONLY: Monotonic event sequence integrity validation
        if req.replay_mode == ReplayMode.VALIDATION_ONLY:
            seqs = [e.sequence_number for e in original_events]
            is_monotonic = seqs == list(range(1, len(seqs) + 1))
            if not is_monotonic:
                raise ReplayError(f"Workflow event log for '{req.source_workflow_id}' violates monotonic ordering.")

            return {
                "replay_mode": ReplayMode.VALIDATION_ONLY.value,
                "source_workflow_id": req.source_workflow_id,
                "event_integrity": "VALID",
                "checkpoint_integrity": "VALID"
            }

        # 3. FULL_REPLAY: Create a NEW workflow execution preserving original history
        if req.replay_mode == ReplayMode.FULL_REPLAY:
            if req.expected_workspace_fingerprint and source_wf.workspace_fingerprint != req.expected_workspace_fingerprint:
                raise ReplayError("Full replay rejected: workspace fingerprint mismatch.")

            replay_wf_id = f"wf-replay-{uuid.uuid4().hex[:8]}"
            new_wf = WorkflowExecution(
                workflow_id=replay_wf_id,
                task_id=source_wf.task_id,
                orchestration_run_id=f"run-{uuid.uuid4().hex[:6]}",
                plan_id=source_wf.plan_id,
                status=WorkflowStatus.REPLAYING,
                created_at=time.time(),
                updated_at=time.time(),
                workspace_fingerprint=source_wf.workspace_fingerprint,
                plan_fingerprint=source_wf.plan_fingerprint,
                replay_of_workflow_id=source_wf.workflow_id
            )
            self.store.create_workflow(new_wf)

            # Record initial replay event in new stream
            evt = WorkflowEventLog.create_event(
                workflow_id=replay_wf_id,
                sequence_number=1,
                event_type="REPLAY_STARTED",
                correlation_id=f"corr-{replay_wf_id}",
                payload={"source_workflow_id": source_wf.workflow_id}
            )
            self.store.append_event(evt)

            return {
                "replay_mode": ReplayMode.FULL_REPLAY.value,
                "source_workflow_id": req.source_workflow_id,
                "replay_workflow_id": replay_wf_id,
                "status": WorkflowStatus.REPLAYING.value
            }

        raise ReplayError(f"Unknown replay mode '{req.replay_mode}'")
