import os
from typing import List, Set, Optional
from .models import EngineeringPlan
from .errors import PlanValidationError
from .operator_selection import OperatorSelector

class PlanValidator:
    """
    Validates EngineeringPlan objects deterministically prior to execution.
    """
    def __init__(self, selector: Optional[OperatorSelector] = None):
        self.selector = selector or OperatorSelector()

    def validate_plan(self, plan: EngineeringPlan, workspace_root: str) -> None:
        real_root = os.path.realpath(workspace_root)

        if not plan.steps:
            raise PlanValidationError("Engineering plan contains zero steps.")

        step_ids: Set[str] = set()
        for step in plan.steps:
            # 1. Unique step IDs
            if step.step_id in step_ids:
                raise PlanValidationError(f"Duplicate step ID '{step.step_id}' found in plan.")
            step_ids.add(step.step_id)

            # 2. Operator existence & compatibility
            try:
                op = self.selector.select_operator(step.task_type)
            except Exception as e:
                raise PlanValidationError(f"Invalid step '{step.step_id}': {str(e)}")

            # 3. Parameter completeness check
            if not step.parameters:
                raise PlanValidationError(f"Step '{step.step_id}' is missing parameters.")

            # 4. Workspace boundary check on affected files
            for file_path in step.affected_files:
                full_path = os.path.abspath(os.path.join(real_root, file_path))
                try:
                    if os.path.commonpath([real_root, full_path]) != real_root:
                        raise PlanValidationError(f"Step '{step.step_id}' references file '{file_path}' outside workspace boundary.")
                except ValueError:
                    raise PlanValidationError(f"Step '{step.step_id}' references file '{file_path}' outside workspace boundary.")

        # 5. Check dependencies exist in step set
        for step in plan.steps:
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    raise PlanValidationError(f"Step '{step.step_id}' depends on non-existent step '{dep_id}'.")
