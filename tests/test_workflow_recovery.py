import tempfile
import os
import unittest
from engine.orchestrator.durability.models import WorkflowExecution, WorkflowStatus
from engine.orchestrator.durability.store import DurableStore
from engine.orchestrator.durability.checkpoint import CheckpointManager
from engine.orchestrator.durability.recovery import WorkflowRecoveryManager

class TestWorkflowRecovery(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_rec.db")
        self.store = DurableStore(self.db_path)
        self.chk_mgr = CheckpointManager(self.store)
        self.recovery_mgr = WorkflowRecoveryManager(self.store)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_recovery_safety_inspection(self):
        wf = WorkflowExecution("wf-1", "t-1", "r-1", "p-1", WorkflowStatus.RUNNING, workspace_fingerprint="fp1")
        self.store.create_workflow(wf)

        self.chk_mgr.create_checkpoint("wf-1", "t-1", WorkflowStatus.RUNNING, workspace_fingerprint="fp1")

        # Matching workspace hash -> Safe to resume
        safety_ok = self.recovery_mgr.inspect_recovery_safety("wf-1", "fp1")
        self.assertTrue(safety_ok["safe_to_resume"])

        # Mismatched workspace hash -> Unsafe, recovery required!
        safety_mismatch = self.recovery_mgr.inspect_recovery_safety("wf-1", "corrupted_fp")
        self.assertFalse(safety_mismatch["safe_to_resume"])
        self.assertEqual(safety_mismatch["reason"], "WORKSPACE_FINGERPRINT_MISMATCH")

if __name__ == "__main__":
    unittest.main()
