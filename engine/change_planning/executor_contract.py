from abc import ABC, abstractmethod
from typing import Dict, Any
from .models import ChangePlan, ExecutionResultContract

class ChangeExecutorContract(ABC):
    """
    Interface boundary defining execution contract for ChangePlan objects.
    """
    @abstractmethod
    def execute_plan(self, plan: ChangePlan) -> ExecutionResultContract:
        """Executes validated ChangePlan and returns structured ExecutionResultContract."""
        pass
