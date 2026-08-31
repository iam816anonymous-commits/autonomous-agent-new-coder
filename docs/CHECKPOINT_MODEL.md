# Checkpoint Model

## 1. Sequence Checkpoints
Checkpoints (`Checkpoint`) are immutable records created sequentially throughout a workflow execution. Each checkpoint references its `previous_checkpoint_id` and records:
* `sequence_number` (1, 2, 3, ...)
* `workflow_status` (`RUNNING`, `WAITING_FOR_APPROVAL`, `COMPLETED`, `FAILED`)
* `completed_steps` & `pending_steps`
* `workspace_fingerprint` & `plan_fingerprint`
* `execution_state` metadata

## 2. Checkpoint Creation Points
1. Workflow creation
2. Post-planning
3. Before approval gate
4. Before operator step execution
5. After operator step execution
6. Post-verification & workflow completion
