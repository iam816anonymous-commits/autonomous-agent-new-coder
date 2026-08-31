# Orchestration Threat Model & Security Review

## 1. Threat Matrix

| Threat | Attack Vector | Mitigation Strategy | Residual Risk | Test Coverage |
| :--- | :--- | :--- | :--- | :--- |
| **Malicious Task Prompt** | Prompt injection in request string attempting shell escape. | Rule-based regex classification; `shell=False` execution. | Ambiguous classification. | `test_task_classifier.py` |
| **Stale Plan Execution** | Workspace modified after plan generation. | Plan bound to SHA-256 workspace fingerprint. | Concurrent external edit window. | `test_orchestration_security.py` |
| **Stale Proposal Application** | Workspace files modified after proposal generation. | Proposal SHA-256 hash verification & double-apply block. | None (fails closed). | `test_proposal_pipeline.py` |
| **Approval Bypass** | Reusing approval across different plans or workspaces. | `ApprovalDecision` bound to `(task_id, plan_id, proposal_id, workspace_hash)`. | None. | `test_approval_policy.py` |
| **Infinite Replan Loop** | Failing verification continuously triggers replanning. | Enforce `MAX_RETRY_ATTEMPTS=2` and `MAX_REPLAN_ATTEMPTS=1`. | Task fails closed after quota. | `test_orchestration_recovery.py` |
| **Secret Exposure in Audit** | Environment credentials printed in logs/evidence artifacts. | Environment variable sanitization and `[REDACTED_SECRET]` scrubbing. | Unrecognized custom secret patterns. | `test_orchestration_security.py` |
| **Path Traversal Escape** | Malicious paths targeting files outside workspace boundary. | Realpath validation using `os.path.commonpath`. | None. | `test_sandbox_workspace.py` |
