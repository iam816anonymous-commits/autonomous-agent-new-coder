# Idempotency Model

## 1. Step Execution Idempotency
Side-effecting operator execution steps are identified by canonical SHA-256 input fingerprints:
`Fingerprinter.compute_step_input_fingerprint(workflow_id, step, attempt)`

## 2. Guard Logic (`IdempotencyGuard`)
1. Before calling `operator.apply()`, `IdempotencyGuard` checks `durable_step_executions` for matching input fingerprints.
2. If the step is `COMPLETED`, execution is skipped and cached output returned.
3. If the step is `RUNNING` (indicating a crash occurred mid-execution), `IdempotencyViolationError` is raised, forcing fail-closed recovery.
