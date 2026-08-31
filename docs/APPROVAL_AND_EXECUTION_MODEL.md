# Approval and Execution Model

## 1. Approval Binding
`ApprovalDecision` objects strictly bind approval authorization to:
* `task_id`
* `plan_id`
* `proposal_id`
* `workspace_fingerprint` (SHA-256 summary hash)

If any file in the workspace is modified prior to proposal application, `ApprovalPolicy.validate_approval()` rejects the stale approval and fails closed.
