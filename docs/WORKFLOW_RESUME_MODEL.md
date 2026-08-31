# Workflow Resume Model

## 1. Safety Checks Prior to Resume
When `WorkflowResumer.resume_workflow()` is invoked:
1. `WorkflowRecoveryManager` retrieves the latest checkpoint from SQLite storage.
2. The current workspace SHA-256 fingerprint is compared against `checkpoint.workspace_fingerprint`.
3. If fingerprints match, the workflow restores pending steps and resumes cleanly.
4. If fingerprints mismatch, resume fails closed with `RecoveryError("WORKSPACE_FINGERPRINT_MISMATCH")`.
