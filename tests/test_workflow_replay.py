import tempfile
import os
import unittest
from engine.orchestrator.durability.models import WorkflowExecution, WorkflowStatus, ReplayRequest, ReplayMode
from engine.orchestrator.durability.store import DurableStore
from engine.orchestrator.durability.replay import WorkflowReplayEngine
from engine.orchestrator.durability.events import WorkflowEventLog

class TestWorkflowReplay(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_rep.db")
        self.store = DurableStore(self.db_path)
        self.replay_eng = WorkflowReplayEngine(self.store)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_replay_dry_run(self):
        wf = WorkflowExecution("wf-dry", "t-1", "r-1", "p-1", WorkflowStatus.COMPLETED, workspace_fingerprint="fp1")
        self.store.create_workflow(wf)

        req = ReplayRequest("wf-dry", "USER", ReplayMode.DRY_RUN)
        res = self.replay_eng.replay_workflow(req)
        self.assertEqual(res["decision"], "DRY_RUN_RECONSTRUCTION_SUCCESS")

    def test_full_replay_creates_new_workflow(self):
        wf = WorkflowExecution("wf-orig", "t-1", "r-1", "p-1", WorkflowStatus.COMPLETED, workspace_fingerprint="fp1")
        self.store.create_workflow(wf)

        evt = WorkflowEventLog.create_event("wf-orig", 1, "WORKFLOW_STARTED", "corr-1")
        self.store.append_event(evt)

        req = ReplayRequest("wf-orig", "USER", ReplayMode.FULL_REPLAY, expected_workspace_fingerprint="fp1")
        res = self.replay_eng.replay_workflow(req)

        self.assertIn("replay_workflow_id", res)
        self.assertNotEqual(res["replay_workflow_id"], "wf-orig")

        # Original workflow remains untouched
        orig_wf = self.store.get_workflow("wf-orig")
        self.assertEqual(orig_wf.status, WorkflowStatus.COMPLETED)

if __name__ == "__main__":
    unittest.main()
