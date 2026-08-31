import os
import tempfile
import unittest
import time
from engine.models import TaskRecord, TaskState, ActorType, SCHEMA_VERSION
from engine.store import TaskStore, ConcurrencyError
from engine.state_machine import TaskStateMachine, InvalidStateTransitionError
from engine.artifacts import ArtifactManager

class TestTaskStorePersistence(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_tasks.db")
        self.store = TaskStore(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_create_get_task(self):
        record = TaskRecord(
            task_id="",
            repository_root="/tmp/repo",
            request="Rename calculate_total to calculate_invoice_total",
            status=TaskState.RECEIVED
        )
        created = self.store.create_task(record)
        self.assertTrue(created.task_id.startswith("TASK-"))

        retrieved = self.store.get_task(created.task_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.request, "Rename calculate_total to calculate_invoice_total")
        self.assertEqual(retrieved.status, TaskState.RECEIVED)
        self.assertEqual(retrieved.schema_version, SCHEMA_VERSION)

    def test_restart_persistence(self):
        record = TaskRecord(
            task_id="TASK-PERSIST-001",
            repository_root="/tmp/repo",
            request="Upgrade dependency X",
            status=TaskState.RECEIVED
        )
        self.store.create_task(record)

        # Simulate process restart by instantiating a new TaskStore
        new_store = TaskStore(self.db_path)
        persisted = new_store.get_task("TASK-PERSIST-001")

        self.assertIsNotNone(persisted)
        self.assertEqual(persisted.request, "Upgrade dependency X")
        events = new_store.get_task_events("TASK-PERSIST-001")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].from_state, TaskState.RECEIVED)


class TestStateTransitions(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_transitions.db")
        self.store = TaskStore(self.db_path)
        self.sm = TaskStateMachine(self.store)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_valid_lifecycle(self):
        task = self.store.create_task(TaskRecord(
            task_id="",
            repository_root="/tmp/repo",
            request="Add DELETE /users/:id",
            status=TaskState.RECEIVED
        ))
        t_id = task.task_id

        self.sm.transition(t_id, TaskState.ANALYZING, "Started analysis")
        self.sm.transition(t_id, TaskState.PLANNED, "Plan generated")
        self.sm.transition(t_id, TaskState.EXECUTING, "Execution started")
        self.sm.transition(t_id, TaskState.VERIFYING, "Running tests")
        self.sm.transition(t_id, TaskState.READY_TO_APPLY, "Verification passed")
        self.sm.transition(t_id, TaskState.APPLYING, "Applying patch")
        final_task = self.sm.transition(t_id, TaskState.COMPLETED, "Completed successfully")

        self.assertEqual(final_task.status, TaskState.COMPLETED)

        events = self.store.get_task_events(t_id)
        self.assertEqual(len(events), 8)

    def test_illegal_transition(self):
        task = self.store.create_task(TaskRecord(
            task_id="",
            repository_root="/tmp/repo",
            request="Add route",
            status=TaskState.RECEIVED
        ))

        with self.assertRaises(InvalidStateTransitionError):
            self.sm.transition(task.task_id, TaskState.COMPLETED, "Shortcut attempt")

    def test_terminal_state_protection(self):
        task = self.store.create_task(TaskRecord(
            task_id="",
            repository_root="/tmp/repo",
            request="Task",
            status=TaskState.RECEIVED
        ))
        t_id = task.task_id

        self.sm.transition(t_id, TaskState.ANALYZING, "Analyzing")
        self.sm.transition(t_id, TaskState.CANCELLED, "User cancelled")

        with self.assertRaises(InvalidStateTransitionError):
            self.sm.transition(t_id, TaskState.ANALYZING, "Try revive")

    def test_idempotent_transition(self):
        task = self.store.create_task(TaskRecord(
            task_id="",
            repository_root="/tmp/repo",
            request="Task",
            status=TaskState.RECEIVED
        ))
        t_id = task.task_id

        self.sm.transition(t_id, TaskState.ANALYZING, "Analyzing")
        res = self.sm.transition(t_id, TaskState.ANALYZING, "Analyzing again")
        self.assertEqual(res.status, TaskState.ANALYZING)


class TestOptimisticConcurrency(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_concurrency.db")
        self.store1 = TaskStore(self.db_path)
        self.store2 = TaskStore(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_concurrency_rejection(self):
        task = self.store1.create_task(TaskRecord(
            task_id="TASK-CONCUR-001",
            repository_root="/tmp/repo",
            request="Parallel task",
            status=TaskState.RECEIVED
        ))

        # Store 1 updates state (version 1 -> 2)
        self.store1.update_task_state_atomic(
            task_id="TASK-CONCUR-001",
            from_state=TaskState.RECEIVED,
            to_state=TaskState.ANALYZING,
            expected_version=1,
            reason="Store 1 analyzing"
        )

        # Store 2 attempts update assuming stale version 1 -> raises ConcurrencyError
        with self.assertRaises(ConcurrencyError):
            self.store2.update_task_state_atomic(
                task_id="TASK-CONCUR-001",
                from_state=TaskState.RECEIVED,
                to_state=TaskState.CANCELLED,
                expected_version=1,
                reason="Store 2 cancelling"
            )


class TestLeaseAndHeartbeat(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_lease.db")
        self.store = TaskStore(self.db_path)
        self.sm = TaskStateMachine(self.store)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_lease_heartbeat_and_stale_recovery(self):
        task = self.store.create_task(TaskRecord(
            task_id="TASK-LEASE-001",
            repository_root="/tmp/repo",
            request="Leased execution",
            status=TaskState.RECEIVED
        ))
        self.sm.transition("TASK-LEASE-001", TaskState.ANALYZING, "Analyzing")
        self.sm.transition("TASK-LEASE-001", TaskState.PLANNED, "Planned")
        self.sm.transition("TASK-LEASE-001", TaskState.EXECUTING, "Executing")

        # Acquire lease
        self.assertTrue(self.sm.acquire_lease("TASK-LEASE-001", "worker-node-1"))
        self.assertTrue(self.sm.heartbeat("TASK-LEASE-001", "worker-node-1"))

        # Immediately check stale leases with timeout 100s -> 0 stale
        stale = self.sm.recover_stale_leases(lease_timeout_seconds=100.0)
        self.assertEqual(len(stale), 0)

        # Test stale recovery with negative timeout (simulates expired lease)
        stale = self.sm.recover_stale_leases(lease_timeout_seconds=-1.0)
        self.assertEqual(len(stale), 1)
        self.assertEqual(stale[0].task_id, "TASK-LEASE-001")
        self.assertEqual(stale[0].status, TaskState.RECOVERY_REQUIRED)


class TestCrashSimulationAndRecovery(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_crash.db")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_crash_recovery(self):
        # 1. Process 1 creates task and advances to EXECUTING
        store1 = TaskStore(self.db_path)
        sm1 = TaskStateMachine(store1)
        task = store1.create_task(TaskRecord(
            task_id="TASK-CRASH-001",
            repository_root="/tmp/repo",
            request="Long running refactor",
            status=TaskState.RECEIVED
        ))
        sm1.transition("TASK-CRASH-001", TaskState.ANALYZING, "Analyzing")
        sm1.transition("TASK-CRASH-001", TaskState.PLANNED, "Planned")
        sm1.transition("TASK-CRASH-001", TaskState.EXECUTING, "Executing codemod")

        # 2. Process 1 terminates unexpectedly
        del sm1
        del store1

        # 3. Process 2 starts up and recovers interrupted tasks
        store2 = TaskStore(self.db_path)
        sm2 = TaskStateMachine(store2)

        recovered = sm2.recover_interrupted_tasks()
        self.assertEqual(len(recovered), 1)
        self.assertEqual(recovered[0].task_id, "TASK-CRASH-001")
        self.assertEqual(recovered[0].status, TaskState.RECOVERY_REQUIRED)

        # Verify task is NOT falsely marked COMPLETED
        retrieved = store2.get_task("TASK-CRASH-001")
        self.assertNotEqual(retrieved.status, TaskState.COMPLETED)
        self.assertEqual(retrieved.status, TaskState.RECOVERY_REQUIRED)


class TestArtifactSecurity(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.manager = ArtifactManager(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_artifact_path_traversal_rejection(self):
        # Malformed task ID with path traversal
        with self.assertRaises(ValueError):
            self.manager.get_task_artifact_dir("../../../etc")

        # Valid task ID
        path = self.manager.write_artifact("TASK-001", "diff.patch", "--- a/foo\n+++ b/foo")
        self.assertTrue(os.path.exists(path))
        self.assertTrue(path.startswith(os.path.realpath(self.temp_dir.name)))


class TestNoLLMRequirement(unittest.TestCase):
    def test_offline_operation(self):
        temp_dir = tempfile.TemporaryDirectory()
        db_path = os.path.join(temp_dir.name, "offline.db")

        store = TaskStore(db_path)
        sm = TaskStateMachine(store)

        t = store.create_task(TaskRecord(
            task_id="",
            repository_root="/tmp/repo",
            request="Offline task",
            status=TaskState.RECEIVED
        ))

        sm.transition(t.task_id, TaskState.ANALYZING, "Offline analysis")
        events = store.get_task_events(t.task_id)

        self.assertEqual(len(events), 2)
        temp_dir.cleanup()

if __name__ == "__main__":
    unittest.main()
