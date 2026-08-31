# 🔄 Task State Machine & Persistent Record (Phase B)

## Overview
Phase B introduces a first-class **Persistent Task State Machine** and append-only **Event Audit Log** for Mini-Jules. This replaces transient in-memory task tracking with SQLite-backed atomic state transitions, optimistic locking, and process crash recovery.

## State Transition Graph

```text
                  RECEIVED
                     │
                     ▼
                 ANALYZING ──────────► CANCELLED / FAILED / BLOCKED
                     │
                     ▼
                  PLANNED
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
  AWAITING_APPROVAL         EXECUTING
          │                     │
          └──────────┬──────────┘
                     ▼
                 VERIFYING ──────────► REPAIRING
                     │                     │
                     ▼                     │
               READY_TO_APPLY ◄────────────┘
                     │
                     ▼
                  APPLYING
                     │
                     ▼
                 COMPLETED
```

## Task States Enum
- **Active Lifecycle**: `RECEIVED`, `ANALYZING`, `PLANNED`, `AWAITING_APPROVAL`, `EXECUTING`, `VERIFYING`, `REPAIRING`, `REVERIFYING`, `READY_TO_APPLY`, `APPLYING`, `COMPLETED`.
- **Terminal & Recovery**: `BLOCKED`, `FAILED`, `CANCELLED`, `ROLLED_BACK`, `RECOVERY_REQUIRED`.

## Key Features

1. **Optimistic Concurrency Control**:
   Every state modification verifies `version = expected_version` and increments version atomically (`version = version + 1`). Parallel transition attempts raise `ConcurrencyError`.

2. **Immutable Event History**:
   State transitions append immutable `TaskEvent` records into `engine_task_events` recording timestamp, actor (`SYSTEM`, `USER`, `AGENT`, `RECOVERY`), `from_state`, `to_state`, and transition reason.

3. **Process Crash Recovery**:
   On system startup, `TaskStateMachine.recover_interrupted_tasks()` scans for tasks left in active non-terminal states (`EXECUTING`, `VERIFYING`, `APPLYING`, etc.) and transitions them to `RECOVERY_REQUIRED`. Interrupted tasks are **never** falsely marked as `COMPLETED`.

4. **100% Offline / Zero-LLM**:
   Task creation, state updates, event history queries, and recovery operations function completely offline without external network or LLM provider dependencies.

## Debug CLI Examples

```bash
# Create a new task record
python -m engine.cli task create --root /path/to/repo --request "Rename calculate_total to calculate_invoice_total"

# Transition task state
python -m engine.cli task transition TASK-123 ANALYZING --reason "Starting repo analysis" --actor SYSTEM

# Inspect task details
python -m engine.cli task get TASK-123

# Inspect immutable audit event log
python -m engine.cli task events TASK-123

# Run process crash recovery
python -m engine.cli task recover
```
