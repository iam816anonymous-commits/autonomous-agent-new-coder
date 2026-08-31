from typing import List, Dict, Set
from .models import EngineeringPlanStep, PlanStepStatus
from .errors import PlanValidationError

class PlanDependencyGraph:
    """
    Manages dependency graph execution, cycle detection, and topological sorting for EngineeringPlan steps.
    """
    def __init__(self, steps: List[EngineeringPlanStep]):
        self.steps: Dict[str, EngineeringPlanStep] = {s.step_id: s for s in steps}
        self.in_degree: Dict[str, int] = {s.step_id: 0 for s in steps}
        self.adj_list: Dict[str, List[str]] = {s.step_id: [] for s in steps}
        self._build_graph()

    def _build_graph(self) -> None:
        for s_id, step in self.steps.items():
            for dep_id in step.dependencies:
                if dep_id not in self.steps:
                    raise PlanValidationError(f"Step '{s_id}' references unknown dependency '{dep_id}'")
                self.adj_list[dep_id].append(s_id)
                self.in_degree[s_id] += 1

        self.detect_cycles()

    def detect_cycles(self) -> None:
        """
        Kahn's algorithm cycle detection.
        """
        in_degree = dict(self.in_degree)
        queue = [node for node, deg in in_degree.items() if deg == 0]
        visited_count = 0

        while queue:
            node = queue.pop(0)
            visited_count += 1
            for neighbor in self.adj_list[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count != len(self.steps):
            raise PlanValidationError("Cyclic dependency detected in engineering plan steps!")

    def get_topological_order(self) -> List[EngineeringPlanStep]:
        in_degree = dict(self.in_degree)
        queue = [node for node, deg in in_degree.items() if deg == 0]
        order: List[EngineeringPlanStep] = []

        while queue:
            # Sort queue by order for deterministic tie-breaking
            queue.sort(key=lambda nid: self.steps[nid].order)
            node = queue.pop(0)
            order.append(self.steps[node])
            for neighbor in self.adj_list[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return order

    def get_ready_steps(self) -> List[EngineeringPlanStep]:
        ready = []
        for s_id, step in self.steps.items():
            if step.status == PlanStepStatus.PENDING:
                # Check if all dependencies are VERIFIED or APPLIED
                deps_satisfied = all(
                    self.steps[dep_id].status in (PlanStepStatus.VERIFIED, PlanStepStatus.APPLIED)
                    for dep_id in step.dependencies
                )
                if deps_satisfied:
                    ready.append(step)
        return sorted(ready, key=lambda s: s.order)
