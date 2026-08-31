# Phase G Initial Repository Audit: Durable Workflow Execution

## Executive Summary
This document records the mandatory repository audit prior to building Phase G (**Durable Workflow Execution, Checkpointing, Resume & Deterministic Replay**). Findings are categorized under **VERIFIED**, **PARTIALLY_IMPLEMENTED**, **MISSING**, **RISK**, and **REUSE_EXISTING**.

---

## 1. Component Map & Audit Categories

### 1.1 `engine/store.py` (TaskStore)
* **VERIFIED**: SQLite persistence for `engine_tasks` and `engine_task_events`.
* **VERIFIED**: Optimistic concurrency versioning (`version`), worker lease management (`acquire_lease`, `heartbeat_at`), and immutable event logging.
* **REUSE_EXISTING**: Re-use `DatabaseManager` and SQLite schema patterns for workflow durability persistence rather than introducing a separate database file or engine.

### 1.2 `engine/state_machine.py` (TaskStateMachine)
* **VERIFIED**: Deterministic state transitions (`RECEIVED` → `ANALYZING` → `PLANNED` → `AWAITING_APPROVAL` → `EXECUTING` → `VERIFYING` → `COMPLETED`).
* **VERIFIED**: Crash recovery method `recover_interrupted_tasks()` transitioning crashed active states to `RECOVERY_REQUIRED`.
* **REUSE_EXISTING**: Map `WorkflowStatus` states directly onto `TaskState` to prevent conflicting state machines.

### 1.3 `engine/orchestrator/`
* **VERIFIED**: `EngineeringOrchestrator` runs full lifecycle without LLMs.
* **VERIFIED**: `EngineeringPlan`, `EngineeringPlanStep`, `ProposalPipeline`, `ApprovalPolicy`, `FailureAnalyzer`, `OrchestrationEvidenceCollector`, and `OrchestrationReporter`.
* **MISSING**: Persistent workflow checkpoints (`Checkpoint`), step execution records (`StepExecution`), idempotency key calculation (`IdempotencyGuard`), workflow recovery manager (`WorkflowRecoveryManager`), resumer (`WorkflowResumer`), and deterministic replay engine (`WorkflowReplayEngine`).

### 1.4 `engine/runtime/sandbox/`
* **VERIFIED**: `WorkspaceSnapshotter` streaming SHA-256 file hashing.
* **VERIFIED**: `WorkspaceTransaction` supporting `DISCARD_ALWAYS`, `COMMIT_ON_SUCCESS`, and `READ_ONLY`.
* **REUSE_EXISTING**: Leverage `WorkspaceSnapshotter` summary hashes for `workspace_fingerprint` validation.

---

## 2. Identified Risks & Mitigations

* **RISK**: Duplicate side-effects if a process crashes mid-operator execution. *Mitigation*: Idempotency key tracking and fail-closed state marking (`RECOVERY_REQUIRED`) when execution status is uncertain.
* **RISK**: Approval validity drift when workspace files are externally modified while paused. *Mitigation*: Fingerprint validation comparing current workspace hash against approval `workspace_fingerprint`.
* **RISK**: Replay mutating original execution history. *Mitigation*: Replay creates a new workflow ID (`replay_of_workflow_id`) and isolated event stream.
