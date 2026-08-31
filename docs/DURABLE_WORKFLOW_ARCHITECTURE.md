# Durable Workflow Architecture

## 1. Overview
The **Durable Engineering Workflow Execution Subsystem** (`engine/orchestrator/durability/`) ensures that Mini-Jules orchestration runs persist across process crashes, pause safely for human approvals, reject duplicate side-effects, and support deterministic replay without mutating historical execution logs.

---

## 2. Subsystem Architecture

```text
engine/orchestrator/durability/
├── __init__.py
├── models.py         # WorkflowExecution, StepExecution, Checkpoint, ReplayRequest, enums
├── errors.py         # DurabilityError, CheckpointError, IdempotencyViolationError, ReplayError
├── store.py          # DurableStore (SQLite workflows, checkpoints, events, step executions)
├── fingerprints.py   # Fingerprinter (SHA-256 canonical JSON hashing)
├── events.py         # WorkflowEventLog (Append-only secret-redacted event log)
├── checkpoint.py     # CheckpointManager (Sequence-ordered checkpointing & validation)
├── idempotency.py    # IdempotencyGuard (Prevents duplicate side-effects)
├── recovery.py       # WorkflowRecoveryManager (Interrupted workflow crash recovery)
├── resume.py         # WorkflowResumer (Context restoration from safe checkpoints)
└── replay.py         # WorkflowReplayEngine (DRY_RUN, VALIDATION_ONLY, FULL_REPLAY)
```

---

## 3. Operational Guarantees
* **100% Offline & Local**: No LLM, cloud, or network dependencies.
* **Process Crash Resilience**: Sequence checkpoints created before/after every side-effect allow safe resume.
* **Idempotency Protection**: Execution step input/output fingerprints prevent double application of operator modifications.
