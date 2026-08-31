from typing import List, Dict, Optional
from .base import EngineeringOperator
from engine.classifier.models import TaskType

class OperatorRegistry:
    """
    Registry for Mini-Jules Engineering Operators.
    """
    def __init__(self):
        self._operators: Dict[str, EngineeringOperator] = {}
        self._task_map: Dict[TaskType, EngineeringOperator] = {}

    def register(self, operator: EngineeringOperator):
        self._operators[operator.name] = operator
        for tt in operator.supported_task_types:
            self._task_map[tt] = operator

    def get_operator_by_name(self, name: str) -> Optional[EngineeringOperator]:
        return self._operators.get(name)

    def get_operator_for_task(self, task_type: TaskType) -> Optional[EngineeringOperator]:
        return self._task_map.get(task_type)

    def list_operators(self) -> List[EngineeringOperator]:
        return list(self._operators.values())
