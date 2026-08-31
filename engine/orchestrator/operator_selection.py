from typing import Optional
from engine.classifier.models import TaskType
from engine.operators.registry import OperatorRegistry
from engine.operators.base import EngineeringOperator
from engine.operators.builtin.symbol_rename import SymbolRenameOperator
from engine.operators.builtin.file_move import FileMoveOperator
from repository.models import RepositorySnapshot
from .errors import OperatorAmbiguityError, PlanningError

class OperatorSelector:
    """
    Deterministically maps TaskType to EngineeringOperator with explicit priority ordering.
    """
    def __init__(self, registry: Optional[OperatorRegistry] = None):
        if registry is not None:
            self.registry = registry
        else:
            self.registry = OperatorRegistry()
            self.registry.register(SymbolRenameOperator())
            self.registry.register(FileMoveOperator())

    def select_operator(self, task_type: TaskType, repo_snapshot: Optional[RepositorySnapshot] = None) -> EngineeringOperator:
        # Strict mapping without guessing
        op = self.registry.get_operator_for_task(task_type)
        if not op:
            raise PlanningError(f"No registered engineering operator available for task type '{task_type.value}'.")
        return op
