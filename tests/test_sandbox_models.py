import os
import tempfile
import unittest
import time
from engine.runtime.sandbox.models import (
    SandboxSpec, SandboxMode, SandboxStatus, FilesystemAccess, NetworkAccess,
    ExecutionCapability, ExecutionTrustLevel, TransactionPolicy, ResourceLimits, ExecutionApproval
)
from engine.runtime.sandbox.capabilities import CapabilitySet
from engine.runtime.sandbox.errors import CapabilityViolationError, ApprovalExpiredError
from engine.runtime.sandbox.snapshot import WorkspaceSnapshotter, FileChangeType
from engine.runtime.sandbox.workspace import WorkspaceManager, WorkspaceEscapeError
from engine.runtime.sandbox.transaction import WorkspaceTransaction, TransactionError

class TestSandboxCoreModels(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_capability_deny_by_default(self):
        caps = CapabilitySet([ExecutionCapability.STATIC_ANALYSIS])
        self.assertTrue(caps.has(ExecutionCapability.STATIC_ANALYSIS))
        self.assertFalse(caps.has(ExecutionCapability.EXECUTE_COMMAND))
        self.assertFalse(caps.has(ExecutionCapability.RUN_TESTS))
        self.assertFalse(caps.has(ExecutionCapability.NETWORK))

        with self.assertRaises(CapabilityViolationError):
            caps.require(ExecutionCapability.EXECUTE_COMMAND)

    def test_capability_escalation_rejected(self):
        parent = CapabilitySet([ExecutionCapability.STATIC_ANALYSIS, ExecutionCapability.READ_WORKSPACE])
        child_valid = CapabilitySet([ExecutionCapability.STATIC_ANALYSIS])
        child_escalated = CapabilitySet([ExecutionCapability.STATIC_ANALYSIS, ExecutionCapability.RUN_TESTS])

        parent.validate_child(child_valid)  # Should pass without error

        with self.assertRaises(CapabilityViolationError):
            parent.validate_child(child_escalated)

    def test_execution_approval_validation(self):
        fp = "abc123hash"
        approval = ExecutionApproval(
            approval_id="APP-001",
            approved_capabilities={ExecutionCapability.READ_WORKSPACE, ExecutionCapability.EXECUTE_COMMAND, ExecutionCapability.RUN_TESTS},
            workspace_id_or_fingerprint=fp,
            trust_level=ExecutionTrustLevel.UNTRUSTED_REPOSITORY_CODE,
            expires_at=time.time() + 300
        )

        # Valid authorization
        self.assertTrue(approval.is_valid_for(fp, ExecutionTrustLevel.UNTRUSTED_REPOSITORY_CODE, {ExecutionCapability.RUN_TESTS}))

        # Mismatched fingerprint
        self.assertFalse(approval.is_valid_for("different_hash", ExecutionTrustLevel.UNTRUSTED_REPOSITORY_CODE, {ExecutionCapability.RUN_TESTS}))

        # Expired approval
        expired_approval = ExecutionApproval(
            approval_id="APP-002",
            approved_capabilities={ExecutionCapability.RUN_TESTS},
            workspace_id_or_fingerprint=fp,
            trust_level=ExecutionTrustLevel.UNTRUSTED_REPOSITORY_CODE,
            expires_at=time.time() - 10
        )
        self.assertFalse(expired_approval.is_valid_for(fp, ExecutionTrustLevel.UNTRUSTED_REPOSITORY_CODE, {ExecutionCapability.RUN_TESTS}))

    def test_streaming_snapshot_and_diff(self):
        f1 = os.path.join(self.root, "a.py")
        with open(f1, "w") as f:
            f.write("print('hello')\n")

        snap_before = WorkspaceSnapshotter.capture(self.root)
        self.assertIn("a.py", snap_before.files)

        # Modify file
        with open(f1, "w") as f:
            f.write("print('world')\n")

        # Add new file
        f2 = os.path.join(self.root, "b.py")
        with open(f2, "w") as f:
            f.write("x = 1\n")

        snap_after = WorkspaceSnapshotter.capture(self.root)
        diff = WorkspaceSnapshotter.diff(snap_before, snap_after)

        self.assertTrue(diff.has_changes)
        change_map = {c.relative_path: c.change_type for c in diff.changes}
        self.assertEqual(change_map.get("a.py"), FileChangeType.MODIFIED)
        self.assertEqual(change_map.get("b.py"), FileChangeType.ADDED)

    def test_workspace_path_and_symlink_escape_protection(self):
        outside_dir = tempfile.TemporaryDirectory()

        # 1. Path traversal escape check
        with self.assertRaises(WorkspaceEscapeError):
            WorkspaceManager.validate_boundary(self.root, os.path.join(self.root, "../outside.txt"))

        # 2. Symlink escape check
        outside_file = os.path.join(outside_dir.name, "secret.txt")
        with open(outside_file, "w") as f:
            f.write("secret")

        symlink_in_ws = os.path.join(self.root, "link_out.txt")
        os.symlink(outside_file, symlink_in_ws)

        with self.assertRaises(WorkspaceEscapeError):
            WorkspaceManager.validate_symlink_target(self.root, symlink_in_ws)

        outside_dir.cleanup()

    def test_transactional_workspace_discard_always(self):
        file1 = os.path.join(self.root, "data.txt")
        with open(file1, "w") as f:
            f.write("initial")

        tx = WorkspaceTransaction(self.root, policy=TransactionPolicy.DISCARD_ALWAYS)
        exec_ws = tx.begin()

        # Modify file in execution workspace
        exec_file1 = os.path.join(exec_ws, "data.txt")
        with open(exec_file1, "w") as f:
            f.write("modified in sandbox")

        diff = tx.end(success=True)
        self.assertTrue(diff.has_changes)

        # Original workspace MUST be unchanged!
        with open(file1) as f:
            self.assertEqual(f.read(), "initial")

if __name__ == "__main__":
    unittest.main()
