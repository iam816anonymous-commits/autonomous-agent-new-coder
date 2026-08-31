import os
import tempfile
import unittest
import time
from engine.runtime.sandbox.models import (
    SandboxSpec, SandboxMode, SandboxStatus, FilesystemAccess, NetworkAccess,
    ExecutionCapability, ExecutionTrustLevel, TransactionPolicy, ExecutionApproval
)
from engine.runtime.sandbox.static_backend import StaticOnlyBackend
from engine.runtime.sandbox.local_backend import RestrictedLocalBackend
from engine.runtime.sandbox.container_backend import ContainerSandboxBackend
from engine.runtime.sandbox.manager import SandboxManager
from engine.runtime.sandbox.errors import CapabilityViolationError, BackendUnavailableError, ApprovalExpiredError
from engine.runtime.sandbox.snapshot import WorkspaceSnapshotter

class TestSandboxBackendsAndIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

        # Create basic python file in workspace
        self.file_path = os.path.join(self.root, "sample.py")
        with open(self.file_path, "w") as f:
            f.write("def add(a, b):\n    return a + b\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_static_only_backend_allows_static_analysis(self):
        spec = SandboxSpec(
            sandbox_id="SB-STATIC-1",
            mode=SandboxMode.STATIC_ONLY,
            workspace_root=self.root,
            allowed_capabilities={ExecutionCapability.STATIC_ANALYSIS, ExecutionCapability.READ_WORKSPACE},
            trust_level=ExecutionTrustLevel.NO_CODE_EXECUTION
        )
        backend = StaticOnlyBackend(spec)
        backend.create()

        self.assertTrue(backend.supports_capability(ExecutionCapability.STATIC_ANALYSIS))
        self.assertFalse(backend.supports_capability(ExecutionCapability.RUN_TESTS))

        # Dynamic command execution attempt must fail-closed in STATIC_ONLY mode
        res = backend.execute("python_syntax_check", ["sample.py"])
        self.assertEqual(res.status, SandboxStatus.FAILED)
        self.assertIn("STATIC_ONLY mode rejects process/command execution attempt", res.execution_result["error"])

    def test_static_only_backend_rejects_dynamic_capability(self):
        spec = SandboxSpec(
            sandbox_id="SB-STATIC-FAIL",
            mode=SandboxMode.STATIC_ONLY,
            workspace_root=self.root,
            allowed_capabilities={ExecutionCapability.STATIC_ANALYSIS, ExecutionCapability.RUN_TESTS},
            trust_level=ExecutionTrustLevel.NO_CODE_EXECUTION
        )
        with self.assertRaises(CapabilityViolationError):
            StaticOnlyBackend(spec)

    def test_restricted_local_backend_execution(self):
        spec = SandboxSpec(
            sandbox_id="SB-LOCAL-1",
            mode=SandboxMode.RESTRICTED_LOCAL,
            workspace_root=self.root,
            allowed_capabilities={ExecutionCapability.READ_WORKSPACE, ExecutionCapability.EXECUTE_COMMAND, ExecutionCapability.RUN_TESTS},
            trust_level=ExecutionTrustLevel.UNTRUSTED_REPOSITORY_CODE
        )
        backend = RestrictedLocalBackend(spec)
        backend.create()

        res = backend.execute("python_syntax_check", ["sample.py"])
        self.assertEqual(res.status, SandboxStatus.COMPLETED)
        self.assertTrue(res.execution_result["success"])
        self.assertIn("Local execution relies on host OS permissions", res.enforcement_metadata["limitations"][0])

    def test_docker_availability_and_fallback(self):
        avail = ContainerSandboxBackend.detect_docker_availability()
        self.assertIn(avail, ["AVAILABLE", "UNAVAILABLE", "MISCONFIGURED"])

        spec = SandboxSpec(
            sandbox_id="SB-DOCKER-1",
            mode=SandboxMode.ISOLATED,
            workspace_root=self.root,
            allowed_capabilities={ExecutionCapability.READ_WORKSPACE, ExecutionCapability.EXECUTE_COMMAND, ExecutionCapability.RUN_TESTS},
            trust_level=ExecutionTrustLevel.UNTRUSTED_REPOSITORY_CODE
        )

        manager = SandboxManager()
        if avail != "AVAILABLE":
            with self.assertRaises(BackendUnavailableError):
                manager.select_backend(spec)
        else:
            backend = manager.select_backend(spec)
            self.assertIsInstance(backend, ContainerSandboxBackend)

    def test_sandbox_manager_approval_and_transaction_flow(self):
        snap = WorkspaceSnapshotter.capture(self.root)
        fp = snap.summary_hash

        spec = SandboxSpec(
            sandbox_id="SB-MGR-1",
            mode=SandboxMode.RESTRICTED_LOCAL,
            workspace_root=self.root,
            allowed_capabilities={ExecutionCapability.READ_WORKSPACE, ExecutionCapability.EXECUTE_COMMAND, ExecutionCapability.RUN_TESTS},
            trust_level=ExecutionTrustLevel.UNTRUSTED_REPOSITORY_CODE,
            transaction_policy=TransactionPolicy.DISCARD_ALWAYS
        )

        manager = SandboxManager()

        # Attempting execution without approval must raise ApprovalExpiredError
        with self.assertRaises(ApprovalExpiredError):
            manager.execute_in_sandbox(spec, "python_syntax_check", ["sample.py"], approval=None)

        # Execution with valid approval
        approval = ExecutionApproval(
            approval_id="APP-MGR-1",
            approved_capabilities={ExecutionCapability.READ_WORKSPACE, ExecutionCapability.EXECUTE_COMMAND, ExecutionCapability.RUN_TESTS},
            workspace_id_or_fingerprint=fp,
            trust_level=ExecutionTrustLevel.UNTRUSTED_REPOSITORY_CODE,
            expires_at=time.time() + 60
        )

        res = manager.execute_in_sandbox(spec, "python_syntax_check", ["sample.py"], approval=approval)
        self.assertEqual(res.status, SandboxStatus.COMPLETED)
        self.assertTrue(res.execution_result["success"])

if __name__ == "__main__":
    unittest.main()
