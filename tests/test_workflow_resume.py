import tempfile
import os
import unittest
from engine.orchestrator.durability.models import WorkflowExecution, WorkflowStatus
from engine.orchestrator.durability.store import DurableStore
from engine.orchestrator.durability.checkpoint import CheckpointManager
from engine.orchestrator.durability.resume import WorkflowResumer

class TestWorkflowResume(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_res.db")
        self.store = DurableStore(self.db_path)
        self.chk_mgr = CheckpointManager(self.store)
        self.resumer = WorkflowResumer(self.store)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_resume_workflow_context_restoration(self):
        wf = WorkflowExecution("wf-10", "t-10", "r-1", "p-1", WorkflowStatus.RUNNING, workspace_fingerprint="fp10")
        self.store.create_workflow(wf)

        self.chk_mgr.create_checkpoint("wf-10", "t-10", WorkflowStatus.RUNNING, completed_steps=["s1"], pending_steps=["s2"], workspace_fingerprint="fp10")

        resumed = self.resumer.resume_workflow("wf-10", "fp10")
        self.assertEqual(resumed["next_step"], "s2")
        self.assertIn("s1", resumed["completed_steps"])

if __name__ == "__main__":
    unittest.main()
