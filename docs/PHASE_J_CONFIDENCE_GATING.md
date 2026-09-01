# Confidence Gating Engine

## 1. Planning Status Decision Matrix
`ConfidenceGatingEngine` evaluates plan confidence and discovery evidence:
* **`READY`**: `HIGH` confidence & `LOW`/`MEDIUM` risk. Execution permitted.
* **`REQUIRES_DISCOVERY`**: `MEDIUM` confidence or insufficient discovery evidence. Re-runs discovery.
* **`REQUIRES_CLARIFICATION`**: `LOW` or `UNKNOWN` confidence. Request user clarification.
* **`HIGH_RISK`**: `HIGH`/`CRITICAL` blast-radius risk. Requires explicit approval.
* **`BLOCKED`**: Conflicting evidence or fail-closed graph error.
