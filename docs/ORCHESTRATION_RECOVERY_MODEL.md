# Orchestration Recovery Model

## 1. Failure Categories
The orchestrator classifies failures into typed `FailureCategory` enums (`STALE_PROPOSAL`, `WORKSPACE_CHANGED`, `APPROVAL_REQUIRED`, `CAPABILITY_DENIED`, `VERIFICATION_FAILURE`, etc.).

## 2. Bounded Quotas
To prevent infinite recursion:
* `MAX_RETRY_ATTEMPTS = 2`
* `MAX_REPLAN_ATTEMPTS = 1`

When retry limits are reached, the transaction is discarded and the task fails closed cleanly.
