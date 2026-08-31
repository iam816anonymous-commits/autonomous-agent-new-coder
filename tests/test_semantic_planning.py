import tempfile
import os
import unittest
from engine.classifier.models import TaskType, TaskClassification, TaskClassificationStatus
from repository.scan import RepositoryAnalyzer
from engine.orchestrator.planner import EngineeringPlanner
from engine.orchestrator.errors import PlanningError

class TestSemanticPlanning(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

        self.file1 = os.path.join(self.root, "calc.py")
        with open(self.file1, "w") as f:
            f.write("def calculate_total(a, b):\n    return a + b\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_planner_requires_discovery_on_unresolved_symbol(self):
        repo_snap = RepositoryAnalyzer.analyze(self.root)
        planner = EngineeringPlanner()

        missing_class = TaskClassification(
            task_type=TaskType.SYMBOL_RENAME,
            status=TaskClassificationStatus.SUPPORTED,
            confidence=0.95,
            extracted_parameters={"old_name": "non_existent_function", "new_name": "foo"}
        )

        with self.assertRaises(PlanningError) as cm:
            planner.create_plan("t1", missing_class, repo_snap)
        self.assertIn("does not exist", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
