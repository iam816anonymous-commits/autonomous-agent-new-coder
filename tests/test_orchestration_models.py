import unittest
from engine.classifier.models import TaskType, TaskClassification, TaskClassificationStatus
from repository.scan import RepositoryAnalyzer
from engine.orchestrator.models import OrchestrationState, PlanStepStatus, FailureCategory, EngineeringPlan, EngineeringPlanStep
from engine.orchestrator.planner import EngineeringPlanner
from engine.orchestrator.plan_validator import PlanValidator, PlanValidationError
from engine.orchestrator.dag import PlanDependencyGraph
from engine.orchestrator.operator_selection import OperatorSelector
from engine.orchestrator.approval import ApprovalPolicy, ApprovalDecision
from engine.orchestrator.errors import PlanningError

class TestOrchestratorPlannerAndModels(unittest.TestCase):
    def setUp(self):
        self.snapshot = RepositoryAnalyzer.analyze(".")
        self.classification = TaskClassification(
            task_type=TaskType.SYMBOL_RENAME,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=0.95,
            extracted_parameters={"old_name": "foo", "new_name": "bar"}
        )

    def test_planner_creates_valid_plan(self):
        planner = EngineeringPlanner()
        plan = planner.create_plan("TASK-001", self.classification, self.snapshot)

        self.assertEqual(plan.task_id, "TASK-001")
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(plan.steps[0].task_type, TaskType.SYMBOL_RENAME)

    def test_planner_fails_closed_on_ambiguous_classification(self):
        planner = EngineeringPlanner()
        ambiguous_class = TaskClassification(
            task_type=TaskType.UNKNOWN_OR_AMBIGUOUS,
            status=TaskClassificationStatus.AMBIGUOUS,
            confidence=0.2,
            extracted_parameters={"reason": "Ambiguous prompt"}
        )
        with self.assertRaises(PlanningError):
            planner.create_plan("TASK-002", ambiguous_class, self.snapshot)

    def test_plan_validator_detects_cycles_and_missing_params(self):
        validator = PlanValidator()
        plan = EngineeringPlan(
            plan_id="p1", task_id="t1", repository_fingerprint="f1",
            task_classification=self.classification,
            steps=[
                EngineeringPlanStep("s1", 1, TaskType.SYMBOL_RENAME, "SymbolRenameOperator", parameters={}, dependencies=["s2"]),
                EngineeringPlanStep("s2", 2, TaskType.SYMBOL_RENAME, "SymbolRenameOperator", parameters={"old_name": "x"}, dependencies=["s1"])
            ]
        )
        with self.assertRaises(PlanValidationError):
            validator.validate_plan(plan, ".")

    def test_dag_cycle_detection(self):
        step1 = EngineeringPlanStep("s1", 1, TaskType.SYMBOL_RENAME, "SymbolRenameOperator", dependencies=["s2"])
        step2 = EngineeringPlanStep("s2", 2, TaskType.SYMBOL_RENAME, "SymbolRenameOperator", dependencies=["s1"])

        with self.assertRaises(PlanValidationError):
            PlanDependencyGraph([step1, step2])

    def test_approval_policy_invalidation(self):
        appr = ApprovalPolicy.create_approval("t1", "p1", "prop1", "hash_before")
        self.assertTrue(ApprovalPolicy.validate_approval(appr, "t1", "p1", "prop1", "hash_before"))

        # Modified workspace fingerprint invalidates approval!
        self.assertFalse(ApprovalPolicy.validate_approval(appr, "t1", "p1", "prop1", "hash_modified"))

if __name__ == "__main__":
    unittest.main()
