# Workflow Event Model

## 1. Event Log Design
Workflow events (`WorkflowEvent`) are appended to `durable_workflow_events` as an immutable, monotonically ordered audit stream.

## 2. Event Types
* `WORKFLOW_STARTED`
* `PLAN_GENERATED`
* `PROPOSAL_GENERATED`
* `APPROVAL_REQUESTED`
* `STEP_STARTED`
* `STEP_COMPLETED`
* `STEP_FAILED`
* `WORKFLOW_COMPLETED`
* `REPLAY_STARTED`

## 3. Secret Redaction
All event payloads automatically redact keys containing sensitive words (`api_key`, `password`, `token`, `secret`, `auth`) or prefixes (`sk-`, `bearer `), replacing them with `[REDACTED_SECRET]`.
