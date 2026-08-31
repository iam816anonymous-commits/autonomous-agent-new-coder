# Phase G Research: Durable Workflow Execution Architecture

## 1. Architectural Principles

Mini-Jules implements a lightweight deterministic orchestration model inspired by general durable workflow principles, not a third-party orchestration framework.

### 1.1 Durable Execution & Sequence Checkpointing
* **Principle**: Workflows progress as a sequence of atomic, checkpointed state transitions.
* **Guarantee**: If a process crashes at step $N$, the engine restores state from Checkpoint $N-1$ or Checkpoint $N$ without re-executing completed side-effects.

### 1.2 Idempotency & Side-Effect Safety
* **Principle**: Side-effecting operations (e.g. operator file mutations) are assigned canonical idempotency keys derived from `(workflow_id, step_id, attempt_number, input_fingerprint)`.
* **Guarantee**: Before executing an operator, the engine checks whether a completed step execution matches the idempotency key.

### 1.3 Exactly-Once Side Effects vs At-Least-Once Replay
* **Principle**: Replaying a workflow (`WorkflowReplayEngine`) must never mutate the original workflow's event log or history.
* **Modes**:
  - `DRY_RUN`: Reconstructs plan decisions without file modifications.
  - `VALIDATION_ONLY`: Validates event log monotonically without operator execution.
  - `FULL_REPLAY`: Spawns a new workflow execution (`replay_of_workflow_id`) with fresh event streams.

### 1.4 Approval Pause & Resume Durability
* **Principle**: Approval pauses release process leases safely. Approvals are cryptographically bound to `(task_id, plan_id, proposal_id, workspace_fingerprint)`.
* **Guarantee**: Resuming a paused workflow validates that the workspace fingerprint matches the approval fingerprint before resuming.
