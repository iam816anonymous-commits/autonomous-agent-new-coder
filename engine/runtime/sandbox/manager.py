import os
import time
import json
from typing import Dict, Any, List, Optional
from .models import SandboxSpec, SandboxResult, SandboxMode, SandboxStatus, ExecutionApproval, ExecutionTrustLevel, ExecutionCapability
from .backend import SandboxBackend
from .static_backend import StaticOnlyBackend
from .local_backend import RestrictedLocalBackend
from .container_backend import ContainerSandboxBackend
from .errors import SandboxError, BackendUnavailableError, ApprovalExpiredError, CapabilityViolationError
from .transaction import WorkspaceTransaction
from .snapshot import WorkspaceSnapshotter
from engine.artifacts import ArtifactManager

class SandboxManager:
    """
    Orchestrates sandbox backend instantiation, execution transaction lifecycle, capability checks, and audit logging.
    """
    def __init__(self, artifact_manager: Optional[ArtifactManager] = None):
        self.artifact_manager = artifact_manager or ArtifactManager()

    def select_backend(self, spec: SandboxSpec) -> SandboxBackend:
        if spec.mode == SandboxMode.STATIC_ONLY:
            return StaticOnlyBackend(spec)
        elif spec.mode == SandboxMode.RESTRICTED_LOCAL:
            return RestrictedLocalBackend(spec)
        elif spec.mode == SandboxMode.ISOLATED:
            avail = ContainerSandboxBackend.detect_docker_availability()
            if avail == "AVAILABLE":
                return ContainerSandboxBackend(spec)
            else:
                raise BackendUnavailableError(f"Container sandbox backend unavailable: Docker status is '{avail}'. Fail-closed.")
        else:
            raise SandboxError(f"Unknown sandbox mode '{spec.mode}'")

    def execute_in_sandbox(
        self,
        spec: SandboxSpec,
        command_name: str,
        args: List[str],
        approval: Optional[ExecutionApproval] = None,
        env: Optional[Dict[str, str]] = None
    ) -> SandboxResult:
        # 1. Validate approval if trust level requires dynamic code execution
        workspace_root = os.path.realpath(spec.workspace_root)
        current_snapshot = WorkspaceSnapshotter.capture(workspace_root)
        fingerprint = current_snapshot.summary_hash

        if spec.trust_level in (ExecutionTrustLevel.TRUSTED_TOOL_ONLY, ExecutionTrustLevel.UNTRUSTED_REPOSITORY_CODE):
            if approval is None:
                raise ApprovalExpiredError("Execution approval required for code execution trust level.")
            if not approval.is_valid_for(fingerprint, spec.trust_level, spec.allowed_capabilities):
                raise ApprovalExpiredError("Provided execution approval is expired, invalid, or does not match workspace fingerprint.")

        # 2. Instantiate backend
        backend = self.select_backend(spec)
        backend.create()
        backend.prepare()

        # 3. Handle Workspace Transaction
        transaction = WorkspaceTransaction(original_workspace=workspace_root, policy=spec.transaction_policy)
        execution_workspace = transaction.begin()
        spec.workspace_root = execution_workspace  # redirect spec to transaction workspace

        # 4. Execute command
        result = backend.execute(command_name, args, env)
        result.snapshot_before_hash = current_snapshot.summary_hash

        # 5. End Transaction
        success = result.status == SandboxStatus.COMPLETED and result.execution_result.get("success", False)
        # Commit requires explicit approval if policy is COMMIT_ON_SUCCESS
        explicit_auth = (approval is not None) and (ExecutionCapability.WRITE_WORKSPACE in approval.approved_capabilities)

        diff = transaction.end(success=success, explicit_commit_auth=explicit_auth)
        if transaction.snapshot_after:
            result.snapshot_after_hash = transaction.snapshot_after.summary_hash

        # 6. Record Audit Artifact
        audit_event = {
            "sandbox_id": spec.sandbox_id,
            "mode": spec.mode.value,
            "trust_level": spec.trust_level.value,
            "backend": backend.__class__.__name__,
            "requested_capabilities": [c.value for c in spec.allowed_capabilities],
            "enforcement_metadata": result.enforcement_metadata,
            "command_name": command_name,
            "args": args,
            "status": result.status.value,
            "snapshot_before": result.snapshot_before_hash,
            "snapshot_after": result.snapshot_after_hash,
            "duration": result.duration,
            "timestamp": time.time()
        }
        self.artifact_manager.write_artifact(f"task_{spec.sandbox_id}", f"sandbox_audit_{int(time.time())}.json", json.dumps(audit_event, indent=2))

        return result
