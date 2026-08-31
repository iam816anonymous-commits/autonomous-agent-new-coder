from typing import Optional, Tuple
from .models import StepExecution, StepStatus
from .store import DurableStore
from .errors import IdempotencyViolationError

class IdempotencyGuard:
    """
    Prevents duplicate side-effects by tracking deterministic step execution input/output fingerprints.
    """
    def __init__(self, store: Optional[DurableStore] = None):
        self.store = store or DurableStore()

    def check_execution_state(self, workflow_id: str, input_fingerprint: str) -> Tuple[bool, Optional[StepExecution]]:
        existing = self.store.get_step_execution_by_input(workflow_id, input_fingerprint)
        if not existing:
            return (False, None)

        if existing.status == StepStatus.COMPLETED:
            # Already completed cleanly!
            return (True, existing)
        elif existing.status == StepStatus.RUNNING:
            # Currently running or crashed mid-execution -> uncertain state!
            raise IdempotencyViolationError(
                f"Conflicting/uncertain execution state for step '{existing.step_id}' with input fingerprint '{input_fingerprint[:12]}'."
            )
        return (False, existing)
