# Phase F Initial Repository Audit

## Executive Summary
This document records the mandatory repository audit prior to building Phase F (**Deterministic Engineering Orchestrator**). All findings are categorized strictly under **VERIFIED**, **INFERRED**, **MISSING**, and **RISK**.

---

## 1. Verified Functionality & Component Map

### 1.1 Repository Knowledge Graph (`repository/`)
* **VERIFIED**: `RepositoryScanner` detects languages, frameworks, package managers, and entry points.
* **VERIFIED**: `SymbolIndexer` extracts AST functions, classes, and methods for Python and pattern-matches JS/TS.
* **VERIFIED**: `DependencyGraphBuilder` builds file/module dependency graphs, detects cycles using DFS, and performs topological sorting.
* **VERIFIED**: `ImpactAnalyzer` performs blast-radius analysis, categorizing impact into `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`.

### 1.2 Persistent Task State Machine & Task Record (`engine/`)
* **VERIFIED**: `TaskStore` provides SQLite persistence with optimistic concurrency control (`version` check).
* **VERIFIED**: `TaskStateMachine` manages explicit transitions (`RECEIVED` → `ANALYZING` → `PLANNED` → `AWAITING_APPROVAL` → `EXECUTING` → `VERIFYING` → `COMPLETED`).
* **VERIFIED**: `TaskEvent` provides append-only immutable audit logging.
* **VERIFIED**: Worker lease acquisition, heartbeat renewal, stale lease recovery, and process crash recovery (`RECOVERY_REQUIRED`).
* **VERIFIED**: `ArtifactManager` provides task artifact persistence with path traversal boundary checking.

### 1.3 Task Classifier (`engine/classifier/`)
* **VERIFIED**: `TaskClassifier` converts natural language into typed `TaskType` classifications (`SYMBOL_RENAME`, `FILE_MOVE`, etc.).
* **VERIFIED**: Parameter extraction via regex and symbol existence validation.
* **VERIFIED**: Severity-ordered numerical risk scoring (`LOW=1`, `MEDIUM=2`, `HIGH=3`, `CRITICAL=4`).

### 1.4 Engineering Operators (`engine/operators/`)
* **VERIFIED**: `OperatorRegistry` maps task types to `EngineeringOperator` implementations.
* **VERIFIED**: `SymbolRenameOperator` uses Python `tokenize` and `ast` for token-level renaming without substring false positives.
* **VERIFIED**: `FileMoveOperator` manages file moving, path escape validation, and dependent import checks.
* **VERIFIED**: Dry-run proposals (`propose()`) generate unified diffs and SHA-256 hashes without workspace mutation.
* **VERIFIED**: Approval boundary checking (`approved=True`), double-apply protection, and targeted transaction rollbacks.

### 1.5 Controlled Verification Runtime & Sandbox (`engine/runtime/`, `engine/runtime/sandbox/`)
* **VERIFIED**: Predefined command registry (`python_syntax_check`, `pytest_targeted`, `pytest_full`, `ruff_lint`).
* **VERIFIED**: Security policy enforcing `shell=False`, argument schema validation, stdout/stderr byte limits, process timeouts, realpath working directory boundaries, and secret redaction (`[REDACTED_SECRET]`).
* **VERIFIED**: `SandboxMode` (`STATIC_ONLY`, `RESTRICTED_LOCAL`, `ISOLATED`).
* **VERIFIED**: `CapabilitySet` enforcing deny-by-default capabilities and child escalation prevention.
* **VERIFIED**: `WorkspaceSnapshotter` streaming SHA-256 file hashing and structured diff calculation.
* **VERIFIED**: `WorkspaceTransaction` supporting `DISCARD_ALWAYS`, `COMMIT_ON_SUCCESS`, and `READ_ONLY` transaction policies.

---

## 2. Inferred Architecture Findings
* **INFERRED**: Orchestrator state (`OrchestrationState`) can map cleanly onto `TaskState` without altering Phase B database schemas or introducing duplicated state machine logic.
* **INFERRED**: The dependency graph of an `EngineeringPlan` (`PlanDependencyGraph`) can use top-level topological sorting to execute multi-step engineering tasks safely in sequence.

---

## 3. Missing Functionality (To Be Implemented in Phase F)
* **MISSING**: High-level `EngineeringPlanner` for converting classifications, impact analysis, and repo snapshots into machine-readable `EngineeringPlan` objects.
* **MISSING**: `PlanValidator` for checking step ordering, capability requirements, and parameter completeness.
* **MISSING**: `ProposalPipeline` for orchestrating dry-run proposals and validating diff hashes prior to approval gates.
* **MISSING**: Scoped `ApprovalPolicy` binding approvals to `(task_id, plan_id, proposal_id, workspace_fingerprint)`.
* **MISSING**: `FailureAnalyzer` and `ReplanningEngine` enforcing bounded retry limits (`MAX_RETRY_ATTEMPTS=2`, `MAX_REPLAN_ATTEMPTS=1`).
* **MISSING**: `OrchestrationEvidenceCollector` and `OrchestrationReporter` for structured audit report generation.
* **MISSING**: `EngineeringOrchestrator` core engine and CLI orchestrate subcommands.

---

## 4. Architectural Risk Assessment
* **RISK**: Workspace modifications occurring between plan generation and execution could cause stale plan application. *Mitigation*: Workspace fingerprint verification before proposal and before execution.
* **RISK**: Failure diagnosis loops causing infinite replanning. *Mitigation*: Hard limits on retries (`MAX_RETRY_ATTEMPTS=2`) and replans (`MAX_REPLAN_ATTEMPTS=1`).
* **RISK**: Approval bypass when re-running tasks. *Mitigation*: Approval invalidation if plan, proposal, or workspace fingerprint changes.
