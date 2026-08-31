import os
import tempfile
import unittest
from engine.runtime.executor import CommandExecutor
from engine.runtime.models import CommandRequest, ExecutionStatus
from engine.runtime.errors import ExecutionApprovalRequiredError

class TestCommandExecutor(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = self.temp_dir.name
        self.executor = CommandExecutor()

        # Create sample Python file
        self.sample_py = os.path.join(self.repo_root, "valid.py")
        with open(self.sample_py, "w") as f:
            f.write("x = 10 + 20\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_low_risk_syntax_check_execution(self):
        req = CommandRequest(
            command_name="python_syntax_check",
            extra_arguments=[self.sample_py]
        )
        res = self.executor.execute(req, self.repo_root, "TASK-EXEC-001", execution_approved=False)

        self.assertEqual(res.status, ExecutionStatus.PASSED)
        self.assertEqual(res.exit_code, 0)
        self.assertTrue(res.duration >= 0)

    def test_high_risk_execution_approval_boundary(self):
        req = CommandRequest(
            command_name="pytest_targeted",
            extra_arguments=["tests/"]
        )

        # execution_approved=False MUST raise ExecutionApprovalRequiredError
        with self.assertRaises(ExecutionApprovalRequiredError):
            self.executor.execute(req, self.repo_root, "TASK-EXEC-002", execution_approved=False)

    def test_timeout_termination(self):
        # Register short timeout command running infinite loop
        from engine.runtime.models import CommandDefinition, CommandCategory, ExecutionRiskLevel
        self.executor.registry.register(CommandDefinition(
            name="infinite_loop_test",
            category=CommandCategory.SYNTAX_CHECK,
            executable="python3",
            base_arguments=["-c", "import time\ntime.sleep(10)"],
            timeout_seconds=0.2,
            risk_level=ExecutionRiskLevel.LOW
        ))

        req = CommandRequest(command_name="infinite_loop_test")
        res = self.executor.execute(req, self.repo_root, "TASK-TIMEOUT-001")

        self.assertEqual(res.status, ExecutionStatus.TIMED_OUT)
        self.assertEqual(res.exit_code, -1)

if __name__ == "__main__":
    unittest.main()
