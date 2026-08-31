import hashlib
import json
from typing import Any, Dict, List
from engine.orchestrator.models import EngineeringPlan, EngineeringPlanStep
from engine.operators.models import ProposedChange

class Fingerprinter:
    """
    Computes deterministic SHA-256 canonical fingerprints for plans, step inputs, proposals, and snapshots.
    """
    @classmethod
    def canonical_json(cls, obj: Any) -> str:
        return json.dumps(obj, sort_keys=True, separators=(',', ':'), default=str)

    @classmethod
    def compute_hash(cls, data_str: str) -> str:
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

    @classmethod
    def compute_plan_fingerprint(cls, plan: EngineeringPlan) -> str:
        serialized_steps = []
        for step in plan.steps:
            serialized_steps.append({
                "step_id": step.step_id,
                "order": step.order,
                "task_type": step.task_type.value,
                "operator_name": step.operator_name,
                "parameters": step.parameters,
                "dependencies": sorted(step.dependencies),
                "affected_files": sorted(step.affected_files)
            })

        payload = {
            "task_id": plan.task_id,
            "risk_level": plan.risk_level,
            "steps": serialized_steps
        }
        return cls.compute_hash(cls.canonical_json(payload))

    @classmethod
    def compute_step_input_fingerprint(cls, workflow_id: str, step: EngineeringPlanStep, attempt: int = 1) -> str:
        payload = {
            "workflow_id": workflow_id,
            "step_id": step.step_id,
            "operator_name": step.operator_name,
            "parameters": step.parameters,
            "attempt": attempt
        }
        return cls.compute_hash(cls.canonical_json(payload))

    @classmethod
    def compute_proposal_fingerprint(cls, proposal: ProposedChange) -> str:
        payload = {
            "operator_name": proposal.operator_name,
            "files_to_modify": sorted([fc.path for fc in proposal.files_to_modify]),
            "files_to_create": sorted([fc.path for fc in proposal.files_to_create]),
            "files_to_delete": sorted(proposal.files_to_delete)
        }
        return cls.compute_hash(cls.canonical_json(payload))
