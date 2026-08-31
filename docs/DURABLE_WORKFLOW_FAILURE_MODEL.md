# Durable Workflow Failure Model

## 1. Failure Categorization
* **Safe Failures**: Verification failure, approval rejection. Action: Discard sandbox transaction, update checkpoint status to `FAILED`.
* **Recoverable Failures**: Process crash during approval pause or before step execution. Action: Inspect checkpoint, verify workspace fingerprint, resume safely.
* **Uncertain / Unsafe Failures**: Process crash mid-operator application or external workspace modification while paused. Action: Mark `RECOVERY_REQUIRED`, require manual intervention / fail closed.
