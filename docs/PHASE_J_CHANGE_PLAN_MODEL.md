# Change Plan Model

## 1. Plan Structures
* **`ChangeRequest`**: `request_id`, `user_intent`, `request_type` (`FEATURE`, `BUG_FIX`, `REFACTOR`, etc.), `constraints`, `target_hints`.
* **`ChangeStep`**: `step_id`, `target_files`, `target_symbols`, `operation_type` (`CREATE`, `MODIFY`, `DELETE`, `MOVE`, `RENAME`), `risk`, `confidence`, `evidence`.
* **`ChangePlan`**: `plan_id`, `request`, `discovery_result`, `impact_analysis`, `steps`, `assertions`, `confidence`, `status` (`PlanningStatus`).
