import os
import sqlite3
import json
import time
import uuid
from typing import List, Dict, Any, Optional, Tuple
from project_creator.core.database.db_manager import DatabaseManager
from .models import TaskRecord, TaskEvent, TaskState, ActorType, SCHEMA_VERSION

class ConcurrencyError(Exception):
    """Raised when an optimistic locking version mismatch occurs."""
    pass

class TaskStore:
    """
    Persistent SQLite storage layer for Mini-Jules Task Records and immutable Task Event histories.
    Includes optimistic concurrency control, schema versioning, and crash recovery queries.
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
                CREATE TABLE IF NOT EXISTS engine_tasks (
                    task_id TEXT PRIMARY KEY,
                    schema_version INTEGER NOT NULL,
                    repository_root TEXT NOT NULL,
                    request TEXT NOT NULL,
                    status TEXT NOT NULL,
                    version INTEGER NOT NULL DEFAULT 1,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    base_commit TEXT,
                    current_commit TEXT,
                    working_branch TEXT,
                    plan TEXT,
                    risk TEXT,
                    change_budget TEXT,
                    expected_files TEXT,
                    changed_files TEXT,
                    test_results TEXT,
                    security_results TEXT,
                    repair_attempts TEXT,
                    error TEXT,
                    artifacts TEXT,
                    metadata TEXT,
                    worker_id TEXT,
                    lease_started_at REAL,
                    heartbeat_at REAL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS engine_task_events (
                    event_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    from_state TEXT NOT NULL,
                    to_state TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY(task_id) REFERENCES engine_tasks(task_id)
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_engine_tasks_status ON engine_tasks(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_engine_events_task ON engine_task_events(task_id)")

    def generate_task_id(self) -> str:
        return f"TASK-{int(time.time())}-{uuid.uuid4().hex[:8]}"

    def _serialize_task(self, record: TaskRecord) -> Tuple:
        return (
            record.task_id,
            record.schema_version,
            record.repository_root,
            record.request,
            record.status.value if isinstance(record.status, TaskState) else str(record.status),
            record.version,
            record.created_at,
            record.updated_at,
            record.base_commit,
            record.current_commit,
            record.working_branch,
            json.dumps(record.plan),
            json.dumps(record.risk),
            json.dumps(record.change_budget),
            json.dumps(record.expected_files),
            json.dumps(record.changed_files),
            json.dumps(record.test_results),
            json.dumps(record.security_results),
            json.dumps(record.repair_attempts),
            record.error,
            json.dumps(record.artifacts),
            json.dumps(record.metadata),
            record.worker_id,
            record.lease_started_at,
            record.heartbeat_at
        )

    def _deserialize_task(self, row: Tuple) -> TaskRecord:
        return TaskRecord(
            task_id=row[0],
            schema_version=row[1],
            repository_root=row[2],
            request=row[3],
            status=TaskState(row[4]),
            version=row[5],
            created_at=row[6],
            updated_at=row[7],
            base_commit=row[8],
            current_commit=row[9],
            working_branch=row[10],
            plan=json.loads(row[11]) if row[11] else {},
            risk=json.loads(row[12]) if row[12] else {},
            change_budget=json.loads(row[13]) if row[13] else {},
            expected_files=json.loads(row[14]) if row[14] else [],
            changed_files=json.loads(row[15]) if row[15] else [],
            test_results=json.loads(row[16]) if row[16] else {},
            security_results=json.loads(row[17]) if row[17] else {},
            repair_attempts=json.loads(row[18]) if row[18] else [],
            error=row[19],
            artifacts=json.loads(row[20]) if row[20] else [],
            metadata=json.loads(row[21]) if row[21] else {},
            worker_id=row[22],
            lease_started_at=row[23],
            heartbeat_at=row[24]
        )

    def create_task(self, record: TaskRecord) -> TaskRecord:
        if not record.task_id:
            record.task_id = self.generate_task_id()

        now = time.time()
        record.created_at = now
        record.updated_at = now

        with self.db_manager.transaction() as cursor:
            cursor.execute("""
                INSERT INTO engine_tasks VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, self._serialize_task(record))

            # Initial RECEIVED event
            event_id = f"EVT-{uuid.uuid4().hex[:10]}"
            cursor.execute("""
                INSERT INTO engine_task_events VALUES (?,?,?,?,?,?,?,?)
            """, (
                event_id,
                record.task_id,
                now,
                TaskState.RECEIVED.value,
                record.status.value if isinstance(record.status, TaskState) else str(record.status),
                "Task Created",
                ActorType.SYSTEM.value,
                json.dumps({})
            ))

        return record

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        with self.db_manager.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM engine_tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            if row:
                return self._deserialize_task(row)
        return None

    def update_task_state_atomic(
        self,
        task_id: str,
        from_state: TaskState,
        to_state: TaskState,
        expected_version: int,
        reason: str,
        actor: ActorType = ActorType.SYSTEM,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TaskRecord:
        """
        Atomically checks version, updates task status, increments version, and appends TaskEvent.
        Raises ConcurrencyError if version mismatch occurs.
        """
        now = time.time()
        metadata_json = json.dumps(metadata or {})
        event_id = f"EVT-{uuid.uuid4().hex[:10]}"

        with self.db_manager.transaction() as cursor:
            # Verify current version & status
            cursor.execute("SELECT version, status FROM engine_tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Task {task_id} not found.")

            current_version, current_status = row[0], row[1]
            if current_version != expected_version:
                raise ConcurrencyError(
                    f"Optimistic concurrency rejection for {task_id}: expected version {expected_version}, but found {current_version}."
                )

            # Perform atomic update
            new_version = current_version + 1
            cursor.execute("""
                UPDATE engine_tasks
                SET status = ?, version = ?, updated_at = ?
                WHERE task_id = ? AND version = ?
            """, (to_state.value, new_version, now, task_id, current_version))

            if cursor.rowcount != 1:
                raise ConcurrencyError(f"Concurrent modification detected during state update for task {task_id}.")

            # Append immutable event
            cursor.execute("""
                INSERT INTO engine_task_events VALUES (?,?,?,?,?,?,?,?)
            """, (
                event_id,
                task_id,
                now,
                from_state.value if isinstance(from_state, TaskState) else str(from_state),
                to_state.value if isinstance(to_state, TaskState) else str(to_state),
                reason,
                actor.value if isinstance(actor, ActorType) else str(actor),
                metadata_json
            ))

            cursor.execute("SELECT * FROM engine_tasks WHERE task_id = ?", (task_id,))
            updated_row = cursor.fetchone()
            return self._deserialize_task(updated_row)

    def update_task(self, record: TaskRecord, expected_version: Optional[int] = None) -> TaskRecord:
        """
        Updates task fields with optional version check.
        """
        now = time.time()
        record.updated_at = now

        with self.db_manager.transaction() as cursor:
            cursor.execute("SELECT version FROM engine_tasks WHERE task_id = ?", (record.task_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Task {record.task_id} not found.")

            current_ver = row[0]
            if expected_version is not None and current_ver != expected_version:
                raise ConcurrencyError(
                    f"Optimistic lock failed: task {record.task_id} version is {current_ver}, expected {expected_version}."
                )

            new_ver = current_ver + 1
            record.version = new_ver

            cursor.execute("""
                UPDATE engine_tasks SET
                    schema_version = ?,
                    repository_root = ?,
                    request = ?,
                    status = ?,
                    version = ?,
                    updated_at = ?,
                    base_commit = ?,
                    current_commit = ?,
                    working_branch = ?,
                    plan = ?,
                    risk = ?,
                    change_budget = ?,
                    expected_files = ?,
                    changed_files = ?,
                    test_results = ?,
                    security_results = ?,
                    repair_attempts = ?,
                    error = ?,
                    artifacts = ?,
                    metadata = ?,
                    worker_id = ?,
                    lease_started_at = ?,
                    heartbeat_at = ?
                WHERE task_id = ? AND version = ?
            """, (
                record.schema_version,
                record.repository_root,
                record.request,
                record.status.value if isinstance(record.status, TaskState) else str(record.status),
                new_ver,
                now,
                record.base_commit,
                record.current_commit,
                record.working_branch,
                json.dumps(record.plan),
                json.dumps(record.risk),
                json.dumps(record.change_budget),
                json.dumps(record.expected_files),
                json.dumps(record.changed_files),
                json.dumps(record.test_results),
                json.dumps(record.security_results),
                json.dumps(record.repair_attempts),
                record.error,
                json.dumps(record.artifacts),
                json.dumps(record.metadata),
                record.worker_id,
                record.lease_started_at,
                record.heartbeat_at,
                record.task_id,
                current_ver
            ))

            if cursor.rowcount != 1:
                raise ConcurrencyError(f"Concurrent update failed for task {record.task_id}.")

        return record

    def update_heartbeat(self, task_id: str, worker_id: str) -> bool:
        now = time.time()
        with self.db_manager.transaction() as cursor:
            cursor.execute("""
                UPDATE engine_tasks
                SET worker_id = ?, heartbeat_at = ?
                WHERE task_id = ?
            """, (worker_id, now, task_id))
            return cursor.rowcount == 1

    def list_tasks(self, status: Optional[TaskState] = None, limit: int = 100) -> List[TaskRecord]:
        with self.db_manager.connection() as conn:
            cursor = conn.cursor()
            if status:
                cursor.execute(
                    "SELECT * FROM engine_tasks WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status.value, limit)
                )
            else:
                cursor.execute("SELECT * FROM engine_tasks ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [self._deserialize_task(r) for r in rows]

    def list_interrupted_tasks(self) -> List[TaskRecord]:
        """Returns tasks left in active, non-terminal execution states."""
        active_states = [
            TaskState.ANALYZING.value,
            TaskState.EXECUTING.value,
            TaskState.VERIFYING.value,
            TaskState.REPAIRING.value,
            TaskState.REVERIFYING.value,
            TaskState.APPLYING.value
        ]
        placeholders = ",".join(["?"] * len(active_states))
        with self.db_manager.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM engine_tasks WHERE status IN ({placeholders}) ORDER BY updated_at ASC",
                active_states
            )
            rows = cursor.fetchall()
            return [self._deserialize_task(r) for r in rows]

    def get_task_events(self, task_id: str) -> List[TaskEvent]:
        with self.db_manager.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM engine_task_events WHERE task_id = ? ORDER BY timestamp ASC",
                (task_id,)
            )
            rows = cursor.fetchall()
            events = []
            for r in rows:
                events.append(TaskEvent(
                    event_id=r[0],
                    task_id=r[1],
                    timestamp=r[2],
                    from_state=TaskState(r[3]),
                    to_state=TaskState(r[4]),
                    reason=r[5],
                    actor=ActorType(r[6]),
                    metadata=json.loads(r[7]) if r[7] else {}
                ))
            return events

    def delete_task(self, task_id: str) -> bool:
        with self.db_manager.transaction() as cursor:
            cursor.execute("DELETE FROM engine_task_events WHERE task_id = ?", (task_id,))
            cursor.execute("DELETE FROM engine_tasks WHERE task_id = ?", (task_id,))
            return cursor.rowcount > 0
