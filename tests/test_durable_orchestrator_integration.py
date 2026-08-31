import tempfile
import os
import unittest
from engine.orchestrator.orchestrator import EngineeringOrchestrator
from engine.orchestrator.models import OrchestrationState
from engine.orchestrator.durability.store import DurableStore

class TestDurableOrchestratorIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name
        self.db_path = os.path.join(self.root, "durable_test.db")
        self.durable_store = DurableStore(self.db_path)

        # Create python project files
        self.utils_path = os.path.join(self.root, "utils.py")
        with open(self.utils_path, "w") as f:
            f.write("def calculate_total(a, b):\n    return a + b\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_durable_orchestrator_checkpoints_workflow(self):
        orchestrator = EngineeringOrchestrator(durable_store=self.durable_store)
        report = orchestrator.run(
            repository_root=self.root,
            request_string="Rename calculate_total to calculate_invoice_total",
            approved=True
        )

        self.assertEqual(report.final_status, OrchestrationState.COMPLETED)

        # Verify durable checkpoints were written to store
        wf_id = f"wf-{report.task_id}"
        checkpoints = self.durable_store.list_checkpoints(wf_id)
        self.assertTrue(len(checkpoints) >= 2)
        self.assertEqual(checkpoints[-1].workflow_status.value, "COMPLETED")

if __name__ == "__main__":
    unittest.main()
