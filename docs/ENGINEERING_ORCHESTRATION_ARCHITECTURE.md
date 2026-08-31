# Engineering Orchestration Architecture

## 1. Overview
The **Deterministic Engineering Orchestrator** (`engine/orchestrator/`) serves as the central control layer for Mini-Jules. It coordinates the complete lifecycle of a software engineering request without relying on an LLM, cloud services, or network access.

---

## 2. End-to-End Orchestration Pipeline

```text
Repository
    │
    ▼
Repository Intelligence (Scanner / Symbol Indexer / Impact Analyzer)
    │
    ▼
Task Classifier (Deterministic Task Classification)
    │
    ▼
Engineering Planner (Plan Creation & Required Capabilities)
    │
    ▼
Plan Validator (Boundary Validation & Cycle Checks)
    │
    ▼
Operator Selector (Priority-based Operator Selection)
    │
    ▼
Proposal Pipeline (Inspect -> Plan -> Propose -> Verify Diff Hashes)
    │
    ▼
Approval Gate (Risk-based Approval Binding to Workspace Fingerprint)
    │
    ▼
Sandbox Transaction (Isolated Copy Execution Workspace)
    │
    ▼
Engineering Operators (Token-level AST Code Transformations)
    │
    ▼
Verification Runtime (Predefined Command Execution & Evidence Collection)
    │
    ▼
Failure Analyzer & Bounded Recovery (Diagnose -> Rollback / Bounded Replan)
    │
    ├──────── PASS ────────► Commit Workspace Transaction & Final Report
    │
    └──────── FAIL ────────► Discard Workspace Copy & Failure Report
```
