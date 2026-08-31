from typing import Dict, List, Optional
from .models import VerificationProfile, CommandCategory, ExecutionRiskLevel, VerificationLevel

DEFAULT_PROFILES: Dict[str, VerificationProfile] = {
    "PYTHON_SYNTAX_ONLY": VerificationProfile(
        profile_id="PYTHON_SYNTAX_ONLY",
        name="Python Syntax Check",
        description="Fast static syntax compilation check only",
        categories=[CommandCategory.SYNTAX_CHECK],
        stop_on_failure=True,
        risk_level=ExecutionRiskLevel.LOW,
        default_level=VerificationLevel.SYNTAX
    ),
    "PYTHON_UNIT_TESTS": VerificationProfile(
        profile_id="PYTHON_UNIT_TESTS",
        name="Python Targeted Unit Tests",
        description="Static syntax check followed by targeted unit tests for affected files",
        categories=[CommandCategory.SYNTAX_CHECK, CommandCategory.TARGETED_TEST],
        stop_on_failure=True,
        risk_level=ExecutionRiskLevel.HIGH,
        default_level=VerificationLevel.TARGETED
    ),
    "PYTHON_FULL_REGRESSION": VerificationProfile(
        profile_id="PYTHON_FULL_REGRESSION",
        name="Python Full Regression Suite",
        description="Syntax check, targeted tests, full test suite, and ruff linter",
        categories=[CommandCategory.SYNTAX_CHECK, CommandCategory.TARGETED_TEST, CommandCategory.FULL_TEST, CommandCategory.LINT],
        stop_on_failure=True,
        risk_level=ExecutionRiskLevel.HIGH,
        default_level=VerificationLevel.FULL
    )
}

def get_profile(profile_id: str) -> Optional[VerificationProfile]:
    return DEFAULT_PROFILES.get(profile_id)
