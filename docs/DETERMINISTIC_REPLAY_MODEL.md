# Deterministic Replay Model

## 1. Replay Modes
* **`DRY_RUN`**: Reconstructs plan step decisions without workspace modifications.
* **`VALIDATION_ONLY`**: Asserts monotonic sequence ordering across event logs and checkpoints.
* **`FULL_REPLAY`**: Executes a new workflow (`replay_of_workflow_id = source_wf_id`), preserving the original workflow's event history completely unchanged.

## 2. History Immutability
Original event logs and checkpoints are read-only and never overwritten during replay operations.
