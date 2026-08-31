import unittest
import time
from engine.orchestrator.durability.models import (
    WorkflowExecution, WorkflowStatus, StepExecution, StepStatus, Checkpoint, ReplayRequest, ReplayMode
)

class TestWorkflowDurabilityModels(unittest.TestCase):
    def test_workflow_execution_instantiation(self):
        wf = WorkflowExecution(
            workflow_id="wf-1",
            task_id="task-1",
            orchestration_run_id="run-1",
            plan_id="plan-1",
            status=WorkflowStatus.RUNNING,
            workspace_fingerprint="hash1",
            plan_fingerprint="hash2"
        )
        self.assertEqual(wf.workflow_id, "wf-1")
        self.assertEqual(wf.status, WorkflowStatus.RUNNING)

    def test_checkpoint_instantiation(self):
        chk = Checkpoint(
            checkpoint_id="chk-1",
            workflow_id="wf-1",
            task_id="task-1",
            sequence_number=1,
            timestamp=time.time(),
            workflow_status=WorkflowStatus.RUNNING,
            completed_steps=["s1"],
            pending_steps=["s2"]
        )
        self.assertEqual(chk.sequence_number, 1)
        self.assertIn("s1", chk.completed_steps)

if __name__ == "__main__":
    unittest.main()
