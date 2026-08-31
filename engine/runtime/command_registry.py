import os
from typing import List, Dict, Optional
from .models import CommandDefinition, CommandCategory, ExecutionRiskLevel
from .policy import RuntimePolicy, BLOCKED_EXECUTABLES
from .errors import CommandRejectedError, PolicyViolationError

class CommandRegistry:
    """
    Registry for Mini-Jules predefined verification commands.
    Strictly rejects shell interpreters, shell injection strings, and unauthorized executables.
    """
    def __init__(self, policy: Optional[RuntimePolicy] = None):
        self.policy = policy or RuntimePolicy()
        self._commands: Dict[str, CommandDefinition] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register(CommandDefinition(
            name="python_syntax_check",
            category=CommandCategory.SYNTAX_CHECK,
            executable="python3",
            base_arguments=["-m", "compileall", "-q"],
            allowed=True,
            timeout_seconds=30.0,
            risk_level=ExecutionRiskLevel.LOW
        ))
        self.register(CommandDefinition(
            name="pytest_targeted",
            category=CommandCategory.TARGETED_TEST,
            executable="pytest",
            base_arguments=[],
            allowed=True,
            timeout_seconds=120.0,
            risk_level=ExecutionRiskLevel.HIGH
        ))
        self.register(CommandDefinition(
            name="pytest_full",
            category=CommandCategory.FULL_TEST,
            executable="pytest",
            base_arguments=[],
            allowed=True,
            timeout_seconds=120.0,
            risk_level=ExecutionRiskLevel.HIGH
        ))
        self.register(CommandDefinition(
            name="ruff_lint",
            category=CommandCategory.LINT,
            executable="ruff",
            base_arguments=["check"],
            allowed=True,
            timeout_seconds=30.0,
            risk_level=ExecutionRiskLevel.MEDIUM
        ))

    def register(self, command: CommandDefinition):
        if command.name in self._commands:
            raise ValueError(f"Duplicate command registration rejected for name '{command.name}'.")

        # Validate executable against policy
        self.policy.validate_executable(command.executable)

        # Check for shell argument injection markers
        for arg in command.base_arguments:
            if any(char in arg for char in [";", "&", "|", "`", "$", ">", "<"]):
                raise PolicyViolationError(
                    f"Command registration rejected for '{command.name}': argument '{arg}' contains shell special characters."
                )

        self._commands[command.name] = command

    def get(self, name: str) -> CommandDefinition:
        cmd = self._commands.get(name)
        if not cmd:
            raise CommandRejectedError(f"Command '{name}' is not registered in the verification runtime registry.")
        if not cmd.allowed:
            raise CommandRejectedError(f"Command '{name}' is explicitly disabled.")
        return cmd

    def list_commands(self) -> List[CommandDefinition]:
        return list(self._commands.values())

    def find_by_category(self, category: CommandCategory) -> List[CommandDefinition]:
        return [cmd for cmd in self._commands.values() if cmd.category == category and cmd.allowed]
