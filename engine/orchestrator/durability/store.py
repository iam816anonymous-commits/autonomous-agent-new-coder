import os
import json
import time
import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from project_creator.core.database.db_manager import DatabaseManager
from .models import WorkflowExecution, Checkpoint, StepExecution, WorkflowStatus, StepStatus
from .events import WorkflowEvent
from .errors import CheckpointError, DurabilityError

class DurableStore:
    """
    SQLite persistence storage layer for workflow executions, sequence checkpoints, append-only workflow events, and step executions.
    """
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.path.join(os.getcwd(), "agent_brain.db")
        self.db_path = db_path
        self.db_manager = DatabaseManager(self.db_path)
        self._init_db()

    def _init_db(self):
        with self.db_manager.transaction() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS durable_workflows (
                    workflow_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    orchestration_run_id TEXT NOT NULL,
                    plan_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    current_checkpoint_id TEXT,
                    workspace_fingerprint TEXT,
                    plan_fingerprint TEXT,
                    retry_count INTEGER DEFAULT 0,
                    replay_of_workflow_id TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS durable_checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    sequence_number INTEGER NOT NULL,
                    timestamp REAL NOT NULL,
                    workflow_status TEXT NOT NULL,
                    current_step TEXT,
                    completed_steps TEXT,
                    pending_steps TEXT,
                    workspace_fingerprint TEXT,
                    plan_fingerprint TEXT,
                    execution_state TEXT,
                    previous_checkpoint_id TEXT,
                    FOREIGN KEY(workflow_id) REFERENCES durable_workflows(workflow_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS durable_workflow_events (
                    event_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    sequence_number INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    correlation_id TEXT NOT NULL,
                    payload TEXT,
                    FOREIGN KEY(workflow_id) REFERENCES durable_workflows(workflow_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS durable_step_executions (
                    step_execution_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    operator_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    proposal_id TEXT,
                    transaction_id TEXT,
                    attempt_number INTEGER DEFAULT 1,
                    input_fingerprint TEXT NOT NULL,
                    output_fingerprint TEXT,
                    started_at REAL NOT NULL,
                    completed_at REAL,
                    error TEXT,
                    FOREIGN KEY(workflow_id) REFERENCES durable_workflows(workflow_id)
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_durable_chk_wf ON durable_checkpoints(workflow_id, sequence_number)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_durable_evt_wf ON durable_workflow_events(workflow_id, sequence_number)")

    def create_workflow(self, wf: WorkflowExecution) -> WorkflowExecution:
        now = time.time()
        wf.created_at = now
        wf.updated_at = now
        with self.db_manager.transaction() as cursor:
            cursor.execute("""
                INSERT INTO durable_workflows VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                wf.workflow_id, wf.task_id, wf.orchestration_run_id, wf.plan_id, wf.status.value,
                wf.created_at, wf.updated_at, wf.current_checkpoint_id, wf.workspace_fingerprint,
                wf.plan_fingerprint, wf.retry_count, wf.replay_of_workflow_id
            ))
        return wf

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowExecution]:
        with self.db_manager.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM durable_workflows WHERE workflow_id = ?", (workflow_id,))
            r = cursor.fetchone()
            if r:
                return WorkflowExecution(
                    workflow_id=r[0], task_id=r[1], orchestration_run_id=r[2], plan_id=r[3],
                    status=WorkflowStatus(r[4]), created_at=r[5], updated_at=r[6], current_checkpoint_id=r[7],
                    workspace_fingerprint=r[8], plan_fingerprint=r[9], retry_count=r[10], replay_of_workflow_id=r[11]
                )
        return None

    def update_workflow_status(self, workflow_id: str, status: WorkflowStatus, current_checkpoint_id: Optional[str] = None) -> None:
        now = time.time()
        with self.db_manager.transaction() as cursor:
            if current_checkpoint_id:
                cursor.execute("""
                    UPDATE durable_workflows SET status = ?, current_checkpoint_id = ?, updated_at = ? WHERE workflow_id = ?
                """, (status.value, current_checkpoint_id, now, workflow_id))
            else:
                cursor.execute("""
                    UPDATE durable_workflows SET status = ?, updated_at = ? WHERE workflow_id = ?
                """, (status.value, now, workflow_id))

    def create_checkpoint(self, chk: Checkpoint) -> Checkpoint:
        with self.db_manager.transaction() as cursor:
            cursor.execute("""
                INSERT INTO durable_checkpoints VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                chk.checkpoint_id, chk.workflow_id, chk.task_id, chk.sequence_number, chk.timestamp,
                chk.workflow_status.value, chk.current_step, json.dumps(chk.completed_steps), json.dumps(chk.pending_steps),
                chk.workspace_fingerprint, chk.plan_fingerprint, json.dumps(chk.execution_state), chk.previous_checkpoint_id
            ))
            cursor.execute("""
                UPDATE durable_workflows SET current_checkpoint_id = ?, status = ?, updated_at = ? WHERE workflow_id = ?
            """, (chk.checkpoint_id, chk.workflow_status.value, chk.timestamp, chk.workflow_id))
        return chk

    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        with self.db_manager.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM durable_checkpoints WHERE checkpoint_id = ?", (checkpoint_id,))
            r = cursor.fetchone()
            if r:
                return Checkpoint(
                    checkpoint_id=r[0], workflow_id=r[1], task_id=r[2], sequence_number=r[3], timestamp=r[4],
                    workflow_status=WorkflowStatus(r[5]), current_step=r[6], completed_steps=json.loads(r[7]),
                    pending_steps=json.loads(r[8]), workspace_fingerprint=r[9], plan_fingerprint=r[10],
                    execution_state=json.loads(r[11]), previous_checkpoint_id=r[12]
                )
        return None

    def get_latest_checkpoint(self, workflow_id: str) -> Optional[Checkpoint]:
        with self.db_manager.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM durable_checkpoints WHERE workflow_id = ? ORDER BY sequence_number DESC LIMIT 1",
                (workflow_id,)
            )
            r = cursor.fetchone()
            if r:
                return Checkpoint(
                    checkpoint_id=r[0], workflow_id=r[1], task_id=r[2], sequence_number=r[3], timestamp=r[4],
                    workflow_status=WorkflowStatus(r[5]), current_step=r[6], completed_steps=json.loads(r[7]),
                    pending_steps=json.loads(r[8]), workspace_fingerprint=r[9], plan_fingerprint=r[10],
                    execution_state=json.loads(r[11]), previous_checkpoint_id=r[12]
                )
        return None

    def list_checkpoints(self, workflow_id: str) -> List[Checkpoint]:
        with self.db_manager.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM durable_checkpoints WHERE workflow_id = ? ORDER BY sequence_number ASC",
                (workflow_id,)
            )
            rows = cursor.fetchall()
            return [
                Checkpoint(
                    checkpoint_id=r[0], workflow_id=r[1], task_id=r[2], sequence_number=r[3], timestamp=r[4],
                    workflow_status=WorkflowStatus(r[5]), current_step=r[6], completed_steps=json.loads(r[7]),
                    pending_steps=json.loads(r[8]), workspace_fingerprint=r[9], plan_fingerprint=r[10],
                    execution_state=json.loads(r[11]), previous_checkpoint_id=r[12]
                ) for r in rows
            ]

    def append_event(self, evt: WorkflowEvent) -> WorkflowEvent:
        with self.db_manager.transaction() as cursor:
            cursor.execute("""
                INSERT INTO durable_workflow_events VALUES (?,?,?,?,?,?,?)
            """, (
                evt.event_id, evt.workflow_id, evt.sequence_number, evt.event_type,
                evt.timestamp, evt.correlation_id, json.dumps(evt.payload)
            ))
        return evt

    def list_events(self, workflow_id: str) -> List[WorkflowEvent]:
        with self.db_manager.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM durable_workflow_events WHERE workflow_id = ? ORDER BY sequence_number ASC",
                (workflow_id,)
            )
            rows = cursor.fetchall()
            return [
                WorkflowEvent(
                    event_id=r[0], workflow_id=r[1], sequence_number=r[2], event_type=r[3],
                    timestamp=r[4], correlation_id=r[5], payload=json.loads(r[6]) if r[6] else {}
                ) for r in rows
            ]

    def create_step_execution(self, step_exec: StepExecution) -> StepExecution:
        with self.db_manager.transaction() as cursor:
            cursor.execute("""
                INSERT INTO durable_step_executions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                step_exec.step_execution_id, step_exec.workflow_id, step_exec.step_id, step_exec.operator_name,
                step_exec.status.value, step_exec.proposal_id, step_exec.transaction_id, step_exec.attempt_number,
                step_exec.input_fingerprint, step_exec.output_fingerprint, step_exec.started_at,
                step_exec.completed_at, step_exec.error
            ))
        return step_exec

    def update_step_execution(self, step_exec: StepExecution) -> StepExecution:
        with self.db_manager.transaction() as cursor:
            cursor.execute("""
                UPDATE durable_step_executions SET
                    status = ?, proposal_id = ?, transaction_id = ?, output_fingerprint = ?, completed_at = ?, error = ?
                WHERE step_execution_id = ?
            """, (
                step_exec.status.value, step_exec.proposal_id, step_exec.transaction_id,
                step_exec.output_fingerprint, step_exec.completed_at, step_exec.error, step_exec.step_execution_id
            ))
        return step_exec

    def get_step_execution_by_input(self, workflow_id: str, input_fingerprint: str) -> Optional[StepExecution]:
        with self.db_manager.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM durable_step_executions WHERE workflow_id = ? AND input_fingerprint = ?",
                (workflow_id, input_fingerprint)
            )
            r = cursor.fetchone()
            if r:
                return StepExecution(
                    step_execution_id=r[0], workflow_id=r[1], step_id=r[2], operator_name=r[3],
                    status=StepStatus(r[4]), proposal_id=r[5], transaction_id=r[6], attempt_number=r[7],
                    input_fingerprint=r[8], output_fingerprint=r[9], started_at=r[10], completed_at=r[11], error=r[12]
                )
        return None
