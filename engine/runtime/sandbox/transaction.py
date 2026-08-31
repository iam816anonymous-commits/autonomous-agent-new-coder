import os
import shutil
from typing import Optional, Dict, Any
from .models import TransactionPolicy
from .errors import TransactionError, WorkspaceEscapeError
from .snapshot import WorkspaceSnapshotter, WorkspaceSnapshot, WorkspaceDiff
from .workspace import WorkspaceManager

class WorkspaceTransaction:
    """
    Encapsulates transactional execution workspace lifecycle.
    Supports DISCARD_ALWAYS, COMMIT_ON_SUCCESS, and READ_ONLY policies.
    """
    def __init__(self, original_workspace: str, policy: TransactionPolicy = TransactionPolicy.DISCARD_ALWAYS):
        self.original_workspace = os.path.realpath(original_workspace)
        self.policy = policy
        self.execution_workspace: Optional[str] = None
        self.snapshot_before: Optional[WorkspaceSnapshot] = None
        self.snapshot_after: Optional[WorkspaceSnapshot] = None
        self.diff: Optional[WorkspaceDiff] = None
        self._committed = False
        self._rolled_back = False

    def begin(self) -> str:
        """
        Captures original snapshot and creates an isolated execution workspace.
        """
        self.snapshot_before = WorkspaceSnapshotter.capture(self.original_workspace)
        if self.policy == TransactionPolicy.READ_ONLY:
            self.execution_workspace = self.original_workspace
        else:
            self.execution_workspace = WorkspaceManager.create_isolated_copy(self.original_workspace)
        return self.execution_workspace

    def end(self, success: bool, explicit_commit_auth: bool = False) -> WorkspaceDiff:
        """
        Evaluates execution outcome, computes diff, and enforces commit/discard policy.
        """
        if self.execution_workspace is None:
            raise TransactionError("Transaction has not been started.")

        self.snapshot_after = WorkspaceSnapshotter.capture(self.execution_workspace)
        self.diff = WorkspaceSnapshotter.diff(self.snapshot_before, self.snapshot_after)

        if self.policy == TransactionPolicy.READ_ONLY:
            # Check if execution illegally modified read-only workspace
            if self.diff.has_changes:
                raise TransactionError("READ_ONLY workspace policy violated: workspace files were modified!")
            return self.diff

        if self.policy == TransactionPolicy.COMMIT_ON_SUCCESS and success:
            if not explicit_commit_auth:
                # Without explicit authorization, default to fail-closed discard
                self.discard()
                raise TransactionError("COMMIT_ON_SUCCESS policy requires explicit commit authorization!")

            self.commit()
        else:
            self.discard()

        return self.diff

    def commit(self) -> None:
        """
        Applies changes from execution workspace back to original workspace after boundary validation.
        """
        if self.policy == TransactionPolicy.READ_ONLY:
            return
        if self._committed or self._rolled_back:
            return

        if self.execution_workspace is None or not os.path.exists(self.execution_workspace):
            raise TransactionError("Execution workspace does not exist for commit.")

        # Re-verify snapshots and validate all target paths before mutating original workspace
        if self.diff is None:
            raise TransactionError("Cannot commit without calculated diff.")

        for change in self.diff.changes:
            target_path = os.path.join(self.original_workspace, change.relative_path)
            # Boundary check target path
            WorkspaceManager.validate_boundary(self.original_workspace, target_path)

            source_path = os.path.join(self.execution_workspace, change.relative_path)

            if change.change_type.value == "DELETED":
                if os.path.exists(target_path):
                    if os.path.isdir(target_path) and not os.path.islink(target_path):
                        shutil.rmtree(target_path)
                    else:
                        os.remove(target_path)
            elif change.change_type.value in ("ADDED", "MODIFIED"):
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                if os.path.islink(source_path):
                    WorkspaceManager.validate_symlink_target(self.execution_workspace, source_path)
                    if os.path.exists(target_path) or os.path.islink(target_path):
                        os.remove(target_path)
                    link_target = os.readlink(source_path)
                    os.symlink(link_target, target_path)
                else:
                    shutil.copy2(source_path, target_path)

        self._committed = True
        self.cleanup()

    def discard(self) -> None:
        """
        Discards isolated execution workspace without modifying original workspace.
        """
        self._rolled_back = True
        self.cleanup()

    def cleanup(self) -> None:
        if self.execution_workspace and self.execution_workspace != self.original_workspace:
            WorkspaceManager.cleanup_workspace(self.execution_workspace)
