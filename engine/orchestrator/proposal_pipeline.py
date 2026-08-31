import os
import hashlib
from typing import Dict, Any, Optional
from engine.operators.base import EngineeringOperator
from engine.operators.models import ProposedChange
from engine.operators.context import OperatorContext
from engine.operators.errors import StaleProposalError
from .errors import PlanningError

class ProposalPipeline:
    """
    Orchestrates inspect -> plan -> propose -> verify_proposal pipeline.
    Ensures dry-run proposals are validated prior to workspace mutations.
    """
    def __init__(self, operator: EngineeringOperator, context: OperatorContext):
        self.operator = operator
        self.context = context

    def generate_proposal(self) -> ProposedChange:
        # 1. Inspect
        inspect_res = self.operator.inspect(self.context)
        can_apply = inspect_res.get("can_apply", False) if isinstance(inspect_res, dict) else True
        if not can_apply:
            reason = inspect_res.get("reason", "Preconditions failed") if isinstance(inspect_res, dict) else "Preconditions failed"
            raise PlanningError(f"Operator inspect rejected execution: {reason}")

        # 2. Plan
        plan_res = self.operator.plan(self.context)

        # 3. Propose
        proposal = self.operator.propose(self.context, plan_res)

        # 4. Verify Proposal (staleness & hash check)
        self.operator.verify_proposal(self.context, proposal)

        return proposal

    @classmethod
    def validate_proposal_freshness(cls, context: OperatorContext, proposal: ProposedChange) -> bool:
        """
        Validates whether workspace files modified in proposal have changed since proposal creation.
        """
        real_root = os.path.realpath(context.repository_root)
        for fc in proposal.files_to_modify:
            full_path = os.path.join(real_root, fc.path)
            if not os.path.exists(full_path):
                if fc.old_sha256 is not None and fc.old_sha256 != "":
                    return False
            else:
                hasher = hashlib.sha256()
                with open(full_path, "rb") as f:
                    hasher.update(f.read())
                current_hash = hasher.hexdigest()
                if fc.old_sha256 and current_hash != fc.old_sha256:
                    return False
        return True
