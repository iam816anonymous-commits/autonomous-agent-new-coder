from dataclasses import asdict
from typing import Optional, Dict, Any, List
from .models import OrchestrationReport, OrchestrationState, EngineeringPlan, ExecutionResult, FailureDiagnosis

class OrchestrationReporter:
    """
    Generates structured, serializable OrchestrationReport objects.
    """
    @classmethod
    def generate_report(
        cls,
        task_id: str,
        request: str,
        classification: Optional[Any] = None,
        repository_summary: Optional[Any] = None,
        plan: Optional[EngineeringPlan] = None,
        results: Optional[List[ExecutionResult]] = None,
        diagnoses: Optional[List[FailureDiagnosis]] = None,
        final_status: OrchestrationState = OrchestrationState.CREATED,
        retries: int = 0,
        replans: int = 0
    ) -> OrchestrationReport:
        results = results or []
        diagnoses = diagnoses or []

        executed_steps = [asdict(r) for r in results if r.status.value in ("APPLIED", "VERIFIED")]
        failures = [asdict(d) for d in diagnoses]
        verifications = [r.verification_result for r in results if r.verification_result]

        # Convert repository summary safely to dict
        if repository_summary is not None:
            if hasattr(repository_summary, "to_dict"):
                repo_dict = repository_summary.to_dict()
            elif hasattr(repository_summary, "__dataclass_fields__"):
                repo_dict = asdict(repository_summary)
            else:
                repo_dict = str(repository_summary)
        else:
            repo_dict = None

        return OrchestrationReport(
            task_id=task_id,
            request=request,
            classification=asdict(classification) if hasattr(classification, "__dataclass_fields__") else classification,
            repository_summary=repo_dict,
            plan=asdict(plan) if hasattr(plan, "__dataclass_fields__") else None,
            executed_steps=executed_steps,
            skipped_steps=[],
            verification_results=verifications,
            failures=failures,
            retries=retries,
            replans=replans,
            workspace_changes=[],
            artifact_references=[f"task_{task_id}"],
            final_status=final_status
        )
