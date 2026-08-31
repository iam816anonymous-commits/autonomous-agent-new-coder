import tempfile
import os
import unittest
from engine.orchestrator.durability.models import WorkflowStatus
from engine.orchestrator.durability.store import DurableStore
from engine.orchestrator.durability.checkpoint import CheckpointManager

class TestWorkflowCheckpoints(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_chk.db")
        self.store = DurableStore(self.db_path)
        self.chk_mgr = CheckpointManager(self.store)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_checkpoint_sequence_increment(self):
        c1 = self.chk_mgr.create_checkpoint("wf-1", "t-1", WorkflowStatus.RUNNING, workspace_fingerprint="fp1")
        self.assertEqual(c1.sequence_number, 1)

        c2 = self.chk_mgr.create_checkpoint("wf-1", "t-1", WorkflowStatus.RUNNING, workspace_fingerprint="fp1")
        self.assertEqual(c2.sequence_number, 2)
        self.assertEqual(c2.previous_checkpoint_id, c1.checkpoint_id)

    def test_checkpoint_consistency_validation(self):
        c1 = self.chk_mgr.create_checkpoint("wf-2", "t-2", WorkflowStatus.RUNNING, workspace_fingerprint="fp_valid")
        self.assertTrue(self.chk_mgr.validate_checkpoint_consistency(c1, "fp_valid"))
        self.assertFalse(self.chk_mgr.validate_checkpoint_consistency(c1, "fp_corrupted"))

if __name__ == "__main__":
    unittest.main()
