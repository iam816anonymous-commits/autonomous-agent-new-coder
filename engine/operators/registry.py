from typing import List, Dict, Optional
from .base import EngineeringOperator
from engine.classifier.models import TaskType

class OperatorRegistry:
    """
    Registry for Mini-Jules Engineering Operators.
    Rejects duplicate operator registrations deterministically.
    """
    def __init__(self):
        self._operators: Dict[str, EngineeringOperator] = {}
        self._task_map: Dict[TaskType, EngineeringOperator] = {}

    def register(self, operator: EngineeringOperator):
        if operator.name in self._operators:
            raise ValueError(f"Duplicate operator registration rejected for operator name '{operator.name}'.")

        for tt in operator.supported_task_types:
            if tt in self._task_map:
                existing = self._task_map[tt].name
                raise ValueError(
                    f"Duplicate operator registration rejected for task type '{tt.value}': "
                    f"already mapped to '{existing}', cannot register '{operator.name}'."
                )

        self._operators[operator.name] = operator
        for tt in operator.supported_task_types:
            self._task_map[tt] = operator

    def get_operator_by_name(self, name: str) -> Optional[EngineeringOperator]:
        return self._operators.get(name)

    def get_operator_for_task(self, task_type: TaskType) -> Optional[EngineeringOperator]:
        return self._task_map.get(task_type)

    def list_operators(self) -> List[EngineeringOperator]:
        return list(self._operators.values())
