import os
import tempfile
import unittest
from engine.runtime.verifier import VerificationPlanner, VerificationRunner
from engine.runtime.models import VerificationStatus
from engine.classifier.models import TaskType, TaskClassificationStatus, TaskClassification
from engine.operators.context import OperatorContext
from engine.operators.builtin.symbol_rename import SymbolRenameOperator
from repository.scan import RepositoryAnalyzer

class TestVerificationRuntime(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

        # Create python project files
        self.utils_path = os.path.join(self.root, "utils.py")
        self.test_path = os.path.join(self.root, "test_utils.py")

        with open(self.utils_path, "w") as f:
            f.write("def calculate_total(a, b):\n    return a + b\n")

        # test_utils.py imports and tests calculate_total
        with open(self.test_path, "w") as f:
            f.write("from utils import calculate_total\n\ndef test_calc():\n    assert calculate_total(1, 2) == 3\n")

        self.snapshot = RepositoryAnalyzer.analyze(self.root)
        self.op = SymbolRenameOperator()

        self.classification = TaskClassification(
            task_type=TaskType.SYMBOL_RENAME,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=0.95,
            extracted_parameters={"old_name": "calculate_total", "new_name": "calculate_invoice_total"}
        )
        self.context = OperatorContext(
            repository_root=self.root,
            task_id="TASK-VERIFY-001",
            classification=self.classification,
            repo_snapshot=self.snapshot
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_verification_planner_impact_integration(self):
        planner = VerificationPlanner()
        plan_res = self.op.plan(self.context)
        proposal = self.op.propose(self.context, plan_res)

        vplan = planner.build_plan(self.context.task_id, proposal, self.snapshot)
        self.assertTrue(len(vplan.steps) >= 1)
        self.assertEqual(vplan.steps[0].command_name, "python_syntax_check")

    def test_verification_runner_success(self):
        planner = VerificationPlanner()
        runner = VerificationRunner()

        plan_res = self.op.plan(self.context)
        proposal = self.op.propose(self.context, plan_res)

        # Apply proposal
        apply_res = self.op.apply(self.context, proposal, approved=True)
        self.assertTrue(apply_res.success)

        # Run verification with execution approval
        vplan = planner.build_plan(self.context.task_id, proposal, self.snapshot)
        vres = runner.run_verification(
            context=self.context,
            proposal=proposal,
            operator=self.op,
            plan=vplan,
            execution_approved=True
        )

        self.assertEqual(vres.status, VerificationStatus.PASSED)
        self.assertFalse(vres.rollback_executed)

    def test_verification_failure_triggers_rollback(self):
        planner = VerificationPlanner()
        runner = VerificationRunner()

        plan_res = self.op.plan(self.context)
        proposal = self.op.propose(self.context, plan_res)

        # Apply proposal
        self.op.apply(self.context, proposal, approved=True)

        # Corrupt file syntax before verification runs
        with open(self.utils_path, "w") as f:
            f.write("def calculate_invoice_total(a, b syntax_error_here\n")

        vplan = planner.build_plan(self.context.task_id, proposal, self.snapshot)
        vres = runner.run_verification(
            context=self.context,
            proposal=proposal,
            operator=self.op,
            plan=vplan,
            execution_approved=True
        )

        # Verification status should be ROLLED_BACK or FAILED
        self.assertIn(vres.status, [VerificationStatus.ROLLED_BACK, VerificationStatus.FAILED])
        self.assertTrue(vres.rollback_executed)

        # Operator targeted rollback restored valid syntax
        with open(self.utils_path) as f:
            self.assertIn("def calculate_total(", f.read())

if __name__ == "__main__":
    unittest.main()
