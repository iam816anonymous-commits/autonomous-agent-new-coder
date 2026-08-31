# Phase F Research: Deterministic Workflow Orchestration

## 1. Executive Summary
Phase F implements the **Deterministic Engineering Orchestrator**, uniting Repository Intelligence, Task Classification, Engineering Planning, Operator Execution, Sandbox Transactions, Verification, Failure Diagnosis, and Crash Recovery into a single fail-closed pipeline.

Crucially, orchestration operates **100% deterministically without LLMs or network access**.

---

## 2. Theoretical Guidance & Primary Concepts

### 2.1 Deterministic Workflow Orchestration
* **VERIFIED FACT**: Workflow engines (e.g., Temporal, Airflow) enforce explicit state transitions and immutable event logs to guarantee crash resilience and determinism.
* **DESIGN INFERENCE**: Mini-Jules uses SQLite-backed append-only event streams (`TaskEvent`) and explicit state transition tables (`TaskStateMachine`) to orchestrate tasks without unhandled intermediate states.

### 2.2 Dependency DAG Execution
* **VERIFIED FACT**: Directed Acyclic Graphs (DAGs) model execution order and dependencies. Topological sorting identifies ready steps while detecting cyclic dependencies prior to execution.
* **PROJECT DECISION**: `PlanDependencyGraph` validates step dependencies, detects cycles via Depth-First Search (DFS), and yields executable steps in deterministic order.

### 2.3 Bounded Re-Planning & Failure Diagnosis
* **VERIFIED FACT**: Unbounded retry loops in autonomous agents lead to infinite recursion and resource exhaustion.
* **PROJECT DECISION**: Failure diagnosis classifies errors into typed `FailureCategory` enums. Retries are strictly bounded (`MAX_RETRY_ATTEMPTS=2`, `MAX_REPLAN_ATTEMPTS=1`). Non-retryable errors fail closed immediately.

---

## 3. Comparative Research & References

1. **Airflow / Temporal Architecture**: Workflow State Persistence & Heartbeats.
2. **Saltzer & Schroeder (1975)**: Least Privilege & Capability Isolation.
3. **OWASP Top 10**: Command & Code Injection Prevention (`shell=False`).
