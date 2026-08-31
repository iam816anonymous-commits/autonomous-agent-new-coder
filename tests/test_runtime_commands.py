import unittest
from engine.runtime.command_registry import CommandRegistry
from engine.runtime.models import CommandDefinition, CommandCategory, ExecutionRiskLevel
from engine.runtime.errors import CommandRejectedError, PolicyViolationError, ArgumentNotAllowedError

class TestCommandRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = CommandRegistry()

    def test_default_commands_registered(self):
        cmd = self.registry.get("python_syntax_check")
        self.assertEqual(cmd.executable, "python3")
        self.assertEqual(cmd.category, CommandCategory.SYNTAX_CHECK)

    def test_duplicate_registration_rejection(self):
        with self.assertRaises(ValueError):
            self.registry.register(CommandDefinition(
                name="python_syntax_check",
                category=CommandCategory.SYNTAX_CHECK,
                executable="python3"
            ))

    def test_blocked_executable_rejection(self):
        with self.assertRaises(PolicyViolationError):
            self.registry.register(CommandDefinition(
                name="blocked_shell",
                category=CommandCategory.FULL_TEST,
                executable="bash",
                base_arguments=["-c", "echo hello"]
            ))

    def test_shell_injection_argument_rejection(self):
        with self.assertRaises(PolicyViolationError):
            self.registry.register(CommandDefinition(
                name="malicious_arg",
                category=CommandCategory.SYNTAX_CHECK,
                executable="python3",
                base_arguments=["|", "rm", "-rf", "/"]
            ))

    def test_extra_argument_schema_validation(self):
        cmd = self.registry.get("python_syntax_check")

        # Valid argument matching pattern
        self.registry.validate_extra_arguments(cmd, ["valid_file.py"])

        # Shell metacharacter in extra arguments raises ArgumentNotAllowedError
        with self.assertRaises(ArgumentNotAllowedError):
            self.registry.validate_extra_arguments(cmd, ["valid_file.py; rm -rf /"])

    def test_unknown_command_rejection(self):
        with self.assertRaises(CommandRejectedError):
            self.registry.get("non_existent_command")

if __name__ == "__main__":
    unittest.main()
