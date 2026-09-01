import tempfile
import os
import unittest
from engine.classifier.models import TaskType, TaskClassification, TaskClassificationStatus
from repository.scan import RepositoryAnalyzer
from engine.orchestrator.planner import EngineeringPlanner
from engine.orchestrator.errors import PlanningError

class TestSemanticPlanningTrust(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

        self.f1 = os.path.join(self.root, "service.py")
        with open(self.f1, "w") as f:
            f.write("def login(user, pwd):\n    return True\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_planning_trust_gate_accepts_high_confidence_symbol(self):
        repo_snap = RepositoryAnalyzer.analyze(self.root)
        planner = EngineeringPlanner()

        classification = TaskClassification(
            task_type=TaskType.SYMBOL_RENAME,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=0.95,
            extracted_parameters={"old_name": "login", "new_name": "authenticate"}
        )

        plan = planner.create_plan("t-trust-1", classification, repo_snap)
        self.assertEqual(plan.task_id, "t-trust-1")

if __name__ == "__main__":
    unittest.main()
