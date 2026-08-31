import time
from dataclasses import dataclass, field
from typing import Set, Optional
from engine.runtime.sandbox.models import ExecutionCapability, ExecutionTrustLevel, ExecutionApproval
from .models import EngineeringPlan
from engine.operators.models import ProposedChange

@dataclass
class ApprovalDecision:
    approval_id: str
    task_id: str
    plan_id: str
    proposal_id: str
    workspace_fingerprint: str
    approved: bool
    approved_capabilities: Set[ExecutionCapability]
    trust_level: ExecutionTrustLevel
    reason: str = ""
    issued_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None

class ApprovalPolicy:
    """
    Evaluates risk and binds approvals strictly to (task_id, plan_id, proposal_id, workspace_fingerprint).
    """
    @classmethod
    def evaluate_approval_requirement(cls, plan: EngineeringPlan) -> bool:
        if plan.risk_level in ("MEDIUM", "HIGH", "CRITICAL") or plan.approval_required:
            return True
        return False

    @classmethod
    def create_approval(
        cls,
        task_id: str,
        plan_id: str,
        proposal_id: str,
        workspace_fingerprint: str,
        trust_level: ExecutionTrustLevel = ExecutionTrustLevel.UNTRUSTED_REPOSITORY_CODE,
        approved_capabilities: Optional[Set[ExecutionCapability]] = None,
        ttl_seconds: float = 300.0
    ) -> ApprovalDecision:
        caps = approved_capabilities or {
            ExecutionCapability.STATIC_ANALYSIS,
            ExecutionCapability.READ_WORKSPACE,
            ExecutionCapability.WRITE_WORKSPACE,
            ExecutionCapability.EXECUTE_COMMAND,
            ExecutionCapability.RUN_TESTS
        }
        return ApprovalDecision(
            approval_id=f"appr-{task_id}-{int(time.time())}",
            task_id=task_id,
            plan_id=plan_id,
            proposal_id=proposal_id,
            workspace_fingerprint=workspace_fingerprint,
            approved=True,
            approved_capabilities=caps,
            trust_level=trust_level,
            issued_at=time.time(),
            expires_at=time.time() + ttl_seconds
        )

    @classmethod
    def validate_approval(
        cls,
        approval: ApprovalDecision,
        task_id: str,
        plan_id: str,
        proposal_id: str,
        current_workspace_fingerprint: str
    ) -> bool:
        if not approval.approved:
            return False
        if approval.expires_at is not None and time.time() > approval.expires_at:
            return False
        if approval.task_id != task_id or approval.plan_id != plan_id or approval.proposal_id != proposal_id:
            return False
        if approval.workspace_fingerprint != current_workspace_fingerprint:
            return False
        return True
