from typing import Dict, Set, List, Optional, Any
from .models import TaskState, ActorType, TaskRecord, TaskEvent
from .store import TaskStore, ConcurrencyError

TRANSITION_GRAPH: Dict[TaskState, Set[TaskState]] = {
    TaskState.RECEIVED: {
        TaskState.ANALYZING,
        TaskState.CANCELLED
    },
    TaskState.ANALYZING: {
        TaskState.PLANNED,
        TaskState.BLOCKED,
        TaskState.FAILED,
        TaskState.CANCELLED
    },
    TaskState.PLANNED: {
        TaskState.AWAITING_APPROVAL,
        TaskState.EXECUTING,
        TaskState.BLOCKED,
        TaskState.FAILED,
        TaskState.CANCELLED
    },
    TaskState.AWAITING_APPROVAL: {
        TaskState.EXECUTING,
        TaskState.CANCELLED,
        TaskState.BLOCKED
    },
    TaskState.EXECUTING: {
        TaskState.VERIFYING,
        TaskState.FAILED,
        TaskState.ROLLED_BACK
    },
    TaskState.VERIFYING: {
        TaskState.REPAIRING,
        TaskState.READY_TO_APPLY,
        TaskState.FAILED,
        TaskState.ROLLED_BACK
    },
    TaskState.REPAIRING: {
        TaskState.REVERIFYING,
        TaskState.FAILED,
        TaskState.ROLLED_BACK
    },
    TaskState.REVERIFYING: {
        TaskState.REPAIRING,
        TaskState.READY_TO_APPLY,
        TaskState.FAILED,
        TaskState.ROLLED_BACK
    },
    TaskState.READY_TO_APPLY: {
        TaskState.APPLYING,
        TaskState.CANCELLED
    },
    TaskState.APPLYING: {
        TaskState.COMPLETED,
        TaskState.FAILED,
        TaskState.ROLLED_BACK
    },
    TaskState.RECOVERY_REQUIRED: {
        TaskState.ANALYZING,
        TaskState.FAILED,
        TaskState.CANCELLED
    },

    # Terminal states
    TaskState.COMPLETED: set(),
    TaskState.FAILED: set(),
    TaskState.CANCELLED: set(),
    TaskState.ROLLED_BACK: set(),
    TaskState.BLOCKED: set()
}

class InvalidStateTransitionError(Exception):
    """Raised when an illegal state transition is attempted."""
    pass

class TaskStateMachine:
    """
    Explicit Task State Machine for Mini-Jules.
    Guarantees deterministic lifecycle transitions, idempotency, lease management, and process crash recovery.
    """
    def __init__(self, store: Optional[TaskStore] = None):
        self.store = store or TaskStore()

    @staticmethod
    def can_transition(from_state: TaskState, to_state: TaskState) -> bool:
        if from_state == to_state:
            return True
        allowed = TRANSITION_GRAPH.get(from_state, set())
        return to_state in allowed

    def transition(
        self,
        task_id: str,
        target_state: TaskState,
        reason: str,
        actor: ActorType = ActorType.SYSTEM,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TaskRecord:
        task = self.store.get_task(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' not found.")

        current_state = task.status

        # Idempotency check: if already in target state, return without error
        if current_state == target_state:
            return task

        # Check transition graph rules
        if not self.can_transition(current_state, target_state):
            raise InvalidStateTransitionError(
                f"Illegal transition for task {task_id}: cannot transition from {current_state.value} to {target_state.value}."
            )

        # Atomic transaction update via store
        updated_task = self.store.update_task_state_atomic(
            task_id=task_id,
            from_state=current_state,
            to_state=target_state,
            expected_version=task.version,
            reason=reason,
            actor=actor,
            metadata=metadata
        )
        return updated_task

    def acquire_lease(self, task_id: str, worker_id: str) -> bool:
        return self.store.acquire_lease(task_id, worker_id)

    def heartbeat(self, task_id: str, worker_id: str) -> bool:
        return self.store.update_heartbeat(task_id, worker_id)

    def recover_interrupted_tasks(self) -> List[TaskRecord]:
        """
        Scans for tasks left in non-terminal execution states following a process crash
        and transitions them to RECOVERY_REQUIRED.
        """
        interrupted = self.store.list_interrupted_tasks()
        recovered_tasks = []

        for task in interrupted:
            try:
                # Force transition to RECOVERY_REQUIRED
                updated = self.store.update_task_state_atomic(
                    task_id=task.task_id,
                    from_state=task.status,
                    to_state=TaskState.RECOVERY_REQUIRED,
                    expected_version=task.version,
                    reason="Process crash detected on startup; recovery required.",
                    actor=ActorType.RECOVERY
                )
                recovered_tasks.append(updated)
            except ConcurrencyError:
                pass # Another worker recovered it

        return recovered_tasks

    def recover_stale_leases(self, lease_timeout_seconds: float = 60.0) -> List[TaskRecord]:
        """
        Scans for active tasks whose worker lease heartbeat has expired and transitions them to RECOVERY_REQUIRED.
        """
        stale = self.store.list_stale_tasks(lease_timeout_seconds=lease_timeout_seconds)
        recovered_tasks = []

        for task in stale:
            try:
                updated = self.store.update_task_state_atomic(
                    task_id=task.task_id,
                    from_state=task.status,
                    to_state=TaskState.RECOVERY_REQUIRED,
                    expected_version=task.version,
                    reason=f"Worker lease expired (no heartbeat for > {lease_timeout_seconds}s); recovery required.",
                    actor=ActorType.RECOVERY
                )
                recovered_tasks.append(updated)
            except ConcurrencyError:
                pass

        return recovered_tasks
