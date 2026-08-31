import os
import tempfile
import unittest
from engine.orchestrator.orchestrator import EngineeringOrchestrator
from engine.orchestrator.models import OrchestrationState
from engine.orchestrator.recovery import FailureAnalyzer, ReplanningEngine
from engine.orchestrator.evidence import OrchestrationEvidenceCollector

class TestOrchestratorCoreAndRecovery(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

        # Create python project files
        self.utils_path = os.path.join(self.root, "utils.py")
        with open(self.utils_path, "w") as f:
            f.write("def calculate_total(a, b):\n    return a + b\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_full_orchestrator_end_to_end_rename_flow(self):
        orchestrator = EngineeringOrchestrator()
        report = orchestrator.run(
            repository_root=self.root,
            request_string="Rename calculate_total to calculate_invoice_total",
            approved=True
        )

        self.assertEqual(report.final_status, OrchestrationState.COMPLETED)
        self.assertTrue(len(report.executed_steps) >= 1)

        # Source file updated
        with open(self.utils_path) as f:
            content = f.read()
            self.assertIn("calculate_invoice_total", content)
            self.assertNotIn("calculate_total", content)

    def test_orchestrator_blocks_when_unapproved(self):
        orchestrator = EngineeringOrchestrator()
        report = orchestrator.run(
            repository_root=self.root,
            request_string="Rename calculate_total to calculate_invoice_total",
            approved=False
        )

        self.assertEqual(report.final_status, OrchestrationState.AWAITING_APPROVAL)

    def test_replanning_engine_retry_limits(self):
        self.assertTrue(ReplanningEngine.can_retry(0))
        self.assertTrue(ReplanningEngine.can_retry(1))
        self.assertFalse(ReplanningEngine.can_retry(2))  # Max 2 retries

        self.assertTrue(ReplanningEngine.can_replan(0))
        self.assertFalse(ReplanningEngine.can_replan(1)) # Max 1 replan

    def test_evidence_collector_secret_redaction(self):
        collector = OrchestrationEvidenceCollector("TASK-SECRET-001")
        collector.record_event("TEST_EVENT", {
            "api_key": "secret_key_12345",
            "normal_param": "public_data"
        })

        self.assertEqual(collector.evidence_log[0]["details"]["api_key"], "[REDACTED_SECRET]")
        self.assertEqual(collector.evidence_log[0]["details"]["normal_param"], "public_data")

if __name__ == "__main__":
    unittest.main()
