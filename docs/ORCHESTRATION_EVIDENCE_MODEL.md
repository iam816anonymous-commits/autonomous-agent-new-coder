# Orchestration Evidence Model

## 1. Evidence Collection
`OrchestrationEvidenceCollector` captures structured JSON event logs throughout every step of the orchestration pipeline.

## 2. Secret Redaction
All evidence logs filter sensitive parameter keys (`api_key`, `password`, `token`, `secret`, `auth`) and string prefixes (`sk-`, `bearer `), replacing them with `[REDACTED_SECRET]`.
