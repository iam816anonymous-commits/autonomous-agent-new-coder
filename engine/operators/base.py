import os
import hashlib
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from .context import OperatorContext
from .models import (
    OperatorPlan,
    ProposedChange,
    VerificationResult,
    ApplyResult,
    FileChange,
    Precondition
)
from .errors import PreconditionFailedError, StaleProposalError, ApprovalRequiredError
from engine.classifier.models import TaskType

def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def is_safe_path(root: str, target: str) -> bool:
    try:
        real_root = os.path.realpath(os.path.abspath(root))
        real_target = os.path.realpath(os.path.abspath(os.path.join(real_root, target)))
        return os.path.commonpath([real_root, real_target]) == real_root
    except Exception:
        return False

class EngineeringOperator(ABC):
    """
    Abstract interface for Mini-Jules Engineering Operators.
    Operates offline without LLMs; enforces dry-run proposals, SHA256 integrity, double-apply protection,
    approval boundaries, and targeted rollbacks.
    """
    def __init__(self, name: str, supported_task_types: List[TaskType], capabilities: List[str]):
        self.name = name
        self.supported_task_types = supported_task_types
        self.capabilities = capabilities

    @abstractmethod
    def inspect(self, context: OperatorContext) -> Dict[str, Any]:
        """Gathers repository state and computes preliminary preconditions (must NOT mutate files)."""
        pass

    @abstractmethod
    def plan(self, context: OperatorContext) -> OperatorPlan:
        """Generates a machine-readable execution plan with preconditions (must NOT mutate files)."""
        pass

    @abstractmethod
    def propose(self, context: OperatorContext, plan: OperatorPlan) -> ProposedChange:
        """
        Dry-run proposal generation.
        Calculates file diffs and SHA256 hashes without modifying any files in the workspace.
        """
        pass

    @abstractmethod
    def verify_proposal(self, context: OperatorContext, proposal: ProposedChange) -> VerificationResult:
        """Verifies proposal integrity before application (must NOT mutate files)."""
        pass

    def is_already_applied(self, context: OperatorContext, proposal: ProposedChange) -> bool:
        """Checks if proposal changes are already present in workspace."""
        if not proposal.files_to_modify and not proposal.files_to_create and not proposal.files_to_delete:
            return False

        # Check files to modify
        for fc in proposal.files_to_modify:
            full_path = os.path.realpath(os.path.abspath(os.path.join(context.repository_root, fc.path)))
            if not os.path.exists(full_path):
                return False
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if compute_sha256(content) != fc.new_sha256:
                return False

        # Check files to create
        for fc in proposal.files_to_create:
            full_path = os.path.realpath(os.path.abspath(os.path.join(context.repository_root, fc.path)))
            if not os.path.exists(full_path):
                return False
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if compute_sha256(content) != fc.new_sha256:
                return False

        # Check files to delete
        for rel_del in proposal.files_to_delete:
            full_path = os.path.realpath(os.path.abspath(os.path.join(context.repository_root, rel_del)))
            if os.path.exists(full_path):
                return False

        return True

    def apply(self, context: OperatorContext, proposal: ProposedChange, approved: bool = False) -> ApplyResult:
        """
        Applies proposed changes to the workspace if approved=True and SHA256 hashes match.
        """
        if not approved:
            raise ApprovalRequiredError(
                f"Approval boundary rejected: operator '{self.name}' requires explicit approved=True to apply changes."
            )

        # 1. Double-apply check
        if self.is_already_applied(context, proposal):
            return ApplyResult(
                success=True,
                transaction_id=proposal.transaction_id,
                files_modified=[fc.path for fc in proposal.files_to_modify],
                files_created=[fc.path for fc in proposal.files_to_create],
                files_deleted=proposal.files_to_delete,
                rollback_available=True,
                error="ALREADY_APPLIED: Proposal changes are already present in workspace."
            )

        # 2. Verify proposal preconditions & content hashes (stale check)
        self.verify_stale_hashes(context, proposal)

        # 3. Execute file mutations and track created backups
        files_modified = []
        files_created = []
        files_deleted = []

        try:
            # Files to modify
            for fc in proposal.files_to_modify:
                if not is_safe_path(context.repository_root, fc.path):
                    raise ValueError(f"Path traversal blocked: {fc.path}")

                full_path = os.path.realpath(os.path.abspath(os.path.join(context.repository_root, fc.path)))
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(fc.new_content or "")
                files_modified.append(fc.path)

            # Files to create
            for fc in proposal.files_to_create:
                if not is_safe_path(context.repository_root, fc.path):
                    raise ValueError(f"Path traversal blocked: {fc.path}")

                full_path = os.path.realpath(os.path.abspath(os.path.join(context.repository_root, fc.path)))
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(fc.new_content or "")
                files_created.append(fc.path)

            # Files to delete
            for rel_path in proposal.files_to_delete:
                if not is_safe_path(context.repository_root, rel_path):
                    raise ValueError(f"Path traversal blocked: {rel_path}")

                full_path = os.path.realpath(os.path.abspath(os.path.join(context.repository_root, rel_path)))
                if os.path.exists(full_path):
                    os.remove(full_path)
                    files_deleted.append(rel_path)

            # 4. Post-verification check
            post_ver = self.verify_proposal(context, proposal)
            if not post_ver.passed:
                self.rollback(context, proposal, files_modified, files_created, files_deleted)
                return ApplyResult(
                    success=False,
                    transaction_id=proposal.transaction_id,
                    error=f"Post-verification failed: {', '.join(post_ver.issues)}. Changes rolled back."
                )

            return ApplyResult(
                success=True,
                transaction_id=proposal.transaction_id,
                files_modified=files_modified,
                files_created=files_created,
                files_deleted=files_deleted,
                rollback_available=True
            )

        except Exception as e:
            self.rollback(context, proposal, files_modified, files_created, files_deleted)
            return ApplyResult(
                success=False,
                transaction_id=proposal.transaction_id,
                error=f"Apply failed: {str(e)}. Transaction rolled back."
            )

    def verify_stale_hashes(self, context: OperatorContext, proposal: ProposedChange):
        for fc in proposal.files_to_modify:
            if not is_safe_path(context.repository_root, fc.path):
                raise ValueError(f"Path traversal blocked: {fc.path}")

            full_path = os.path.realpath(os.path.abspath(os.path.join(context.repository_root, fc.path)))
            if not os.path.exists(full_path):
                raise StaleProposalError(f"Stale proposal: file '{fc.path}' no longer exists.")

            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                current_content = f.read()

            current_sha = compute_sha256(current_content)
            if fc.old_sha256 and current_sha != fc.old_sha256:
                raise StaleProposalError(
                    f"Stale proposal: file '{fc.path}' was modified after proposal generation. "
                    f"Expected SHA256 {fc.old_sha256[:12]}, but found {current_sha[:12]}."
                )

    def rollback(
        self,
        context: OperatorContext,
        proposal: ProposedChange,
        files_modified: Optional[List[str]] = None,
        files_created: Optional[List[str]] = None,
        files_deleted: Optional[List[str]] = None
    ) -> bool:
        """Targeted rollback of operator-owned file changes only."""
        files_to_restore = files_modified or [fc.path for fc in proposal.files_to_modify]
        files_to_remove = files_created or [fc.path for fc in proposal.files_to_create]

        try:
            # Restore modified files
            for fc in proposal.files_to_modify:
                if fc.path in files_to_restore and fc.old_content is not None:
                    if is_safe_path(context.repository_root, fc.path):
                        full_path = os.path.realpath(os.path.abspath(os.path.join(context.repository_root, fc.path)))
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write(fc.old_content)

            # Delete created files
            for fc in proposal.files_to_create:
                if fc.path in files_to_remove:
                    if is_safe_path(context.repository_root, fc.path):
                        full_path = os.path.realpath(os.path.abspath(os.path.join(context.repository_root, fc.path)))
                        if os.path.exists(full_path):
                            os.remove(full_path)

            return True
        except Exception:
            return False
