import os
import re
from typing import List, Dict, Optional
from .models import CommandDefinition, CommandCategory, ExecutionRiskLevel, ExecutionCapability, ExecutionSideEffect
from .policy import RuntimePolicy, BLOCKED_EXECUTABLES
from .errors import CommandRejectedError, PolicyViolationError, ArgumentNotAllowedError

class CommandRegistry:
    """
    Registry for Mini-Jules predefined verification commands.
    Strictly rejects shell interpreters, shell injection strings, and unauthorized executables or arguments.
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
            allowed_argument_patterns=[r'^[a-zA-Z0-9_./-]+$'],
            allowed=True,
            timeout_seconds=30.0,
            risk_level=ExecutionRiskLevel.LOW,
            capabilities=[ExecutionCapability.READ_WORKSPACE, ExecutionCapability.PROCESS_SPAWN],
            side_effect=ExecutionSideEffect.READ_ONLY,
            description="Static Python syntax compilation check"
        ))
        self.register(CommandDefinition(
            name="pytest_targeted",
            category=CommandCategory.TARGETED_TEST,
            executable="pytest",
            base_arguments=[],
            allowed_argument_patterns=[r'^[a-zA-Z0-9_./-]+$', r'^-k$', r'^-v$', r'^-q$', r'^--tb=[a-z]+$'],
            allowed=True,
            timeout_seconds=120.0,
            risk_level=ExecutionRiskLevel.HIGH,
            capabilities=[ExecutionCapability.READ_WORKSPACE, ExecutionCapability.PROCESS_SPAWN],
            side_effect=ExecutionSideEffect.READ_ONLY,
            description="Targeted pytest execution for affected test paths"
        ))
        self.register(CommandDefinition(
            name="pytest_full",
            category=CommandCategory.FULL_TEST,
            executable="pytest",
            base_arguments=[],
            allowed_argument_patterns=[r'^[a-zA-Z0-9_./-]+$', r'^-v$', r'^-q$'],
            allowed=True,
            timeout_seconds=120.0,
            risk_level=ExecutionRiskLevel.HIGH,
            capabilities=[ExecutionCapability.READ_WORKSPACE, ExecutionCapability.PROCESS_SPAWN],
            side_effect=ExecutionSideEffect.READ_ONLY,
            description="Full pytest suite execution"
        ))
        self.register(CommandDefinition(
            name="ruff_lint",
            category=CommandCategory.LINT,
            executable="ruff",
            base_arguments=["check"],
            allowed_argument_patterns=[r'^[a-zA-Z0-9_./-]+$'],
            allowed=True,
            timeout_seconds=30.0,
            risk_level=ExecutionRiskLevel.MEDIUM,
            capabilities=[ExecutionCapability.READ_WORKSPACE, ExecutionCapability.PROCESS_SPAWN],
            side_effect=ExecutionSideEffect.READ_ONLY,
            description="Read-only Ruff linter verification"
        ))

    def register(self, command: CommandDefinition):
        if command.name in self._commands:
            raise ValueError(f"Duplicate command registration rejected for name '{command.name}'.")

        # Validate executable and capabilities against policy
        self.policy.validate_executable(command.executable)
        self.policy.validate_capabilities(command.capabilities)

        # Check for shell argument injection markers in base arguments
        for arg in command.base_arguments:
            if any(char in arg for char in [";", "&", "|", "`", "$", ">", "<"]):
                raise PolicyViolationError(
                    f"Command registration rejected for '{command.name}': argument '{arg}' contains shell special characters."
                )

        self._commands[command.name] = command

    def validate_extra_arguments(self, cmd_def: CommandDefinition, extra_args: List[str]):
        """Validates extra arguments against command's allowed argument patterns."""
        if not extra_args:
            return

        patterns = cmd_def.allowed_argument_patterns
        for arg in extra_args:
            # Rejection of shell metacharacters in extra arguments
            if any(char in arg for char in [";", "&", "|", "`", "$", ">", "<"]):
                raise ArgumentNotAllowedError(
                    f"Argument Rejection: Extra argument '{arg}' contains shell metacharacters."
                )

            if patterns:
                matched = any(re.match(p, arg) for p in patterns)
                if not matched:
                    raise ArgumentNotAllowedError(
                        f"Argument Rejection: Argument '{arg}' does not match allowed patterns for command '{cmd_def.name}'."
                    )

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
