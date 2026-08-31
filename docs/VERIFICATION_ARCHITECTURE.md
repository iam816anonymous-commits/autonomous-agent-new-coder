# 🏛️ Controlled Verification Runtime Architecture (Phase E.1)

## Overview
Phase E.1 completes the **Controlled Verification Runtime** (`engine.runtime`). It decouples verification planning from arbitrary execution, enforcing predefined command registries, verification profiles, risk-based execution approval boundaries, and evidence artifact persistence.

## Architecture Pipeline

```text
Applied Proposal
       │
       ▼
VerificationPlanner ──► Selected Profile (PYTHON_UNIT_TESTS, PYTHON_FULL_REGRESSION)
       │
       ▼
  VerificationPlan  ──► Ordered Steps (Syntax Check -> Targeted Tests -> Optional Lint)
       │
       ▼
 CommandRegistry    ──► Resolves Command ID -> Executable & Base Arguments
       │
       ▼
  RuntimePolicy     ──► Validates Executable, Arguments, Workspace Boundary & Capabilities
       │
       ▼
LocalRestrictedEnv ──► Executes with shell=False, Timeout, Output Truncation, Secret Redaction
       │
       ▼
Snapshot Validation ──► Compares workspace hash before/after execution
       │
       ▼
VerificationResult ──► PASSED / ROLLED_BACK / APPLIED_BUT_VERIFICATION_FAILED
```

## Verification Profiles
- **`PYTHON_SYNTAX_ONLY`**: Static `compileall` syntax compilation check (`LOW` risk).
- **`PYTHON_UNIT_TESTS`**: Syntax check + Phase A impact-analysis-driven targeted `pytest` (`HIGH` risk, requires `execution_approved=True`).
- **`PYTHON_FULL_REGRESSION`**: Full `pytest` suite + `ruff` linter check.

## Evidence Artifacts
Execution logs and result models are persisted under `task_artifacts/<task_id>/<execution_id>_result.json` using `ArtifactManager`.
