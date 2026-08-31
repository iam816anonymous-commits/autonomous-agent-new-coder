import uuid
from typing import Dict, Any, Optional
from .models import FailureCategory, FailureDiagnosis, ExecutionResult, EngineeringPlan
from .errors import RecoveryError

class FailureAnalyzer:
    """
    Classifies execution/verification failures into typed FailureCategory enums and determines retryability.
    """
    @classmethod
    def diagnose(cls, result: ExecutionResult) -> FailureDiagnosis:
        diag_id = f"diag-{uuid.uuid4().hex[:8]}"
        err_msg = (result.error or "").lower()

        if "stale" in err_msg or "hash mismatch" in err_msg:
            return FailureDiagnosis(
                diagnosis_id=diag_id,
                execution_id=result.execution_id,
                failure_category=FailureCategory.STALE_PROPOSAL,
                evidence={"error": result.error},
                affected_step=result.step_id,
                retryable=True,
                recommended_action="REGENERATE_PROPOSAL"
            )

        if "workspace changed" in err_msg:
            return FailureDiagnosis(
                diagnosis_id=diag_id,
                execution_id=result.execution_id,
                failure_category=FailureCategory.WORKSPACE_CHANGED,
                evidence={"error": result.error},
                affected_step=result.step_id,
                retryable=True,
                recommended_action="REANALYZE_REPOSITORY"
            )

        if "approval" in err_msg or "expired" in err_msg:
            return FailureDiagnosis(
                diagnosis_id=diag_id,
                execution_id=result.execution_id,
                failure_category=FailureCategory.APPROVAL_REQUIRED,
                evidence={"error": result.error},
                affected_step=result.step_id,
                retryable=False,
                recommended_action="REQUEST_EXPLICIT_APPROVAL"
            )

        if "capability" in err_msg or "denied" in err_msg:
            return FailureDiagnosis(
                diagnosis_id=diag_id,
                execution_id=result.execution_id,
                failure_category=FailureCategory.CAPABILITY_DENIED,
                evidence={"error": result.error},
                affected_step=result.step_id,
                retryable=False,
                recommended_action="FAIL_CLOSED"
            )

        if "verification" in err_msg or "syntax" in err_msg or "failed" in err_msg:
            return FailureDiagnosis(
                diagnosis_id=diag_id,
                execution_id=result.execution_id,
                failure_category=FailureCategory.VERIFICATION_FAILURE,
                evidence={"error": result.error, "verification": result.verification_result},
                affected_step=result.step_id,
                retryable=True,
                recommended_action="ROLLBACK_AND_REPLAN"
            )

        return FailureDiagnosis(
            diagnosis_id=diag_id,
            execution_id=result.execution_id,
            failure_category=FailureCategory.UNKNOWN,
            evidence={"error": result.error},
            affected_step=result.step_id,
            retryable=False,
            recommended_action="FAIL_CLOSED"
        )

class ReplanningEngine:
    """
    Manages bounded retries and replanning (MAX_RETRY_ATTEMPTS=2, MAX_REPLAN_ATTEMPTS=1).
    """
    MAX_RETRY_ATTEMPTS = 2
    MAX_REPLAN_ATTEMPTS = 1

    @classmethod
    def can_retry(cls, retry_count: int) -> bool:
        return retry_count < cls.MAX_RETRY_ATTEMPTS

    @classmethod
    def can_replan(cls, replan_count: int) -> bool:
        return replan_count < cls.MAX_REPLAN_ATTEMPTS
