import tempfile
import os
import unittest
import time
from engine.orchestrator.durability.models import StepExecution, StepStatus
from engine.orchestrator.durability.store import DurableStore
from engine.orchestrator.durability.idempotency import IdempotencyGuard
from engine.orchestrator.durability.errors import IdempotencyViolationError

class TestWorkflowIdempotency(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_idemp.db")
        self.store = DurableStore(self.db_path)
        self.guard = IdempotencyGuard(self.store)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_idempotency_detects_already_completed(self):
        step_exec = StepExecution(
            step_execution_id="se-1",
            workflow_id="wf-1",
            step_id="step-1",
            operator_name="SymbolRenameOperator",
            status=StepStatus.COMPLETED,
            input_fingerprint="input_hash_123"
        )
        self.store.create_step_execution(step_exec)

        completed, found_exec = self.guard.check_execution_state("wf-1", "input_hash_123")
        self.assertTrue(completed)
        self.assertIsNotNone(found_exec)

    def test_idempotency_raises_on_uncertain_running_state(self):
        step_exec = StepExecution(
            step_execution_id="se-2",
            workflow_id="wf-2",
            step_id="step-2",
            operator_name="FileMoveOperator",
            status=StepStatus.RUNNING,
            input_fingerprint="input_hash_456"
        )
        self.store.create_step_execution(step_exec)

        with self.assertRaises(IdempotencyViolationError):
            self.guard.check_execution_state("wf-2", "input_hash_456")

if __name__ == "__main__":
    unittest.main()
