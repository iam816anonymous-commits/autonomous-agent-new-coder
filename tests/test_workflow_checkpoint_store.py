import tempfile
import os
import unittest
import time
from engine.orchestrator.durability.models import (
    WorkflowExecution, WorkflowStatus, StepExecution, StepStatus, Checkpoint
)
from engine.orchestrator.durability.events import WorkflowEventLog
from engine.orchestrator.durability.store import DurableStore

class TestWorkflowCheckpointStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_durable.db")
        self.store = DurableStore(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_workflow_and_checkpoint_crud(self):
        wf = WorkflowExecution(
            workflow_id="wf-100",
            task_id="task-100",
            orchestration_run_id="run-1",
            plan_id="plan-1",
            status=WorkflowStatus.RUNNING,
            workspace_fingerprint="ws_hash_123"
        )
        self.store.create_workflow(wf)

        fetched_wf = self.store.get_workflow("wf-100")
        self.assertIsNotNone(fetched_wf)
        self.assertEqual(fetched_wf.task_id, "task-100")

        chk = Checkpoint(
            checkpoint_id="chk-100-1",
            workflow_id="wf-100",
            task_id="task-100",
            sequence_number=1,
            timestamp=time.time(),
            workflow_status=WorkflowStatus.RUNNING,
            completed_steps=["step-1"],
            pending_steps=["step-2"],
            workspace_fingerprint="ws_hash_123"
        )
        self.store.create_checkpoint(chk)

        latest_chk = self.store.get_latest_checkpoint("wf-100")
        self.assertIsNotNone(latest_chk)
        self.assertEqual(latest_chk.sequence_number, 1)

    def test_append_event_and_list_events(self):
        wf = WorkflowExecution("wf-200", "t-200", "r-1", "p-1", WorkflowStatus.RUNNING)
        self.store.create_workflow(wf)

        evt1 = WorkflowEventLog.create_event("wf-200", 1, "WORKFLOW_STARTED", "corr-1", {"req": "test"})
        evt2 = WorkflowEventLog.create_event("wf-200", 2, "STEP_COMPLETED", "corr-1", {"step_id": "s1"})

        self.store.append_event(evt1)
        self.store.append_event(evt2)

        events = self.store.list_events("wf-200")
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].event_type, "WORKFLOW_STARTED")
        self.assertEqual(events[1].event_type, "STEP_COMPLETED")

if __name__ == "__main__":
    unittest.main()
