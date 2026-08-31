from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from .models import VerificationProfile, CommandCategory, ExecutionRiskLevel, VerificationLevel
from .sandbox.models import SandboxMode, ExecutionTrustLevel, ExecutionCapability, TransactionPolicy

@dataclass
class SandboxVerificationProfile(VerificationProfile):
    sandbox_mode: SandboxMode = SandboxMode.STATIC_ONLY
    trust_level: ExecutionTrustLevel = ExecutionTrustLevel.NO_CODE_EXECUTION
    required_capabilities: Set[ExecutionCapability] = field(default_factory=lambda: {ExecutionCapability.STATIC_ANALYSIS, ExecutionCapability.READ_WORKSPACE})
    transaction_policy: TransactionPolicy = TransactionPolicy.READ_ONLY
    executes_repository_code: bool = False
    requires_network_isolation: bool = True
    allows_workspace_writes: bool = False

DEFAULT_PROFILES: Dict[str, SandboxVerificationProfile] = {
    "PYTHON_SYNTAX_ONLY": SandboxVerificationProfile(
        profile_id="PYTHON_SYNTAX_ONLY",
        name="Python Syntax Check",
        description="Fast static syntax compilation check only",
        categories=[CommandCategory.SYNTAX_CHECK],
        stop_on_failure=True,
        risk_level=ExecutionRiskLevel.LOW,
        default_level=VerificationLevel.SYNTAX,
        sandbox_mode=SandboxMode.STATIC_ONLY,
        trust_level=ExecutionTrustLevel.NO_CODE_EXECUTION,
        required_capabilities={ExecutionCapability.STATIC_ANALYSIS, ExecutionCapability.READ_WORKSPACE},
        transaction_policy=TransactionPolicy.READ_ONLY,
        executes_repository_code=False,
        requires_network_isolation=True,
        allows_workspace_writes=False
    ),
    "PYTHON_UNIT_TESTS": SandboxVerificationProfile(
        profile_id="PYTHON_UNIT_TESTS",
        name="Python Targeted Unit Tests",
        description="Static syntax check followed by targeted unit tests for affected files",
        categories=[CommandCategory.SYNTAX_CHECK, CommandCategory.TARGETED_TEST],
        stop_on_failure=True,
        risk_level=ExecutionRiskLevel.HIGH,
        default_level=VerificationLevel.TARGETED,
        sandbox_mode=SandboxMode.RESTRICTED_LOCAL,
        trust_level=ExecutionTrustLevel.UNTRUSTED_REPOSITORY_CODE,
        required_capabilities={ExecutionCapability.READ_WORKSPACE, ExecutionCapability.EXECUTE_COMMAND, ExecutionCapability.RUN_TESTS},
        transaction_policy=TransactionPolicy.DISCARD_ALWAYS,
        executes_repository_code=True,
        requires_network_isolation=True,
        allows_workspace_writes=False
    ),
    "PYTHON_FULL_REGRESSION": SandboxVerificationProfile(
        profile_id="PYTHON_FULL_REGRESSION",
        name="Python Full Regression Suite",
        description="Syntax check, targeted tests, full test suite, and ruff linter",
        categories=[CommandCategory.SYNTAX_CHECK, CommandCategory.TARGETED_TEST, CommandCategory.FULL_TEST, CommandCategory.LINT],
        stop_on_failure=True,
        risk_level=ExecutionRiskLevel.HIGH,
        default_level=VerificationLevel.FULL,
        sandbox_mode=SandboxMode.RESTRICTED_LOCAL,
        trust_level=ExecutionTrustLevel.UNTRUSTED_REPOSITORY_CODE,
        required_capabilities={ExecutionCapability.READ_WORKSPACE, ExecutionCapability.EXECUTE_COMMAND, ExecutionCapability.RUN_TESTS},
        transaction_policy=TransactionPolicy.DISCARD_ALWAYS,
        executes_repository_code=True,
        requires_network_isolation=True,
        allows_workspace_writes=False
    )
}

def get_profile(profile_id: str) -> Optional[VerificationProfile]:
    return DEFAULT_PROFILES.get(profile_id)
