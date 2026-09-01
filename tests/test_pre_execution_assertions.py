import tempfile
import os
import unittest
from engine.change_planning.models import ChangeRequest, ChangeRequestType, ChangePlan, ChangeStep
from engine.change_planning.pre_execution import PreExecutionValidator
from engine.change_planning.errors import PreExecutionAssertionError
from repository.scan import RepositoryAnalyzer
from repository.semantic.snapshot import SemanticSnapshotter

class TestPreExecutionAssertions(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

        self.f1 = os.path.join(self.root, "calc.py")
        with open(self.f1, "w") as f:
            f.write("def add(a, b):\n    return a + b\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pre_execution_validator_passes_valid_plan(self):
        repo_snap = RepositoryAnalyzer.analyze(self.root)
        sem_snap = SemanticSnapshotter.capture(repo_snap)

        req = ChangeRequest("r1", "intent", ChangeRequestType.FEATURE, "desc")
        step = ChangeStep("s1", "desc", target_files=["calc.py"], target_symbols=["add"])
        plan = ChangePlan("p1", req, steps=[step])

        validator = PreExecutionValidator(self.root, sem_snap)
        res = validator.validate_plan_preconditions(plan)
        self.assertTrue(len(res) >= 2)

    def test_pre_execution_validator_fails_on_missing_file(self):
        repo_snap = RepositoryAnalyzer.analyze(self.root)
        sem_snap = SemanticSnapshotter.capture(repo_snap)

        req = ChangeRequest("r1", "intent", ChangeRequestType.FEATURE, "desc")
        step = ChangeStep("s1", "desc", target_files=["non_existent.py"], target_symbols=[])
        plan = ChangePlan("p1", req, steps=[step])

        validator = PreExecutionValidator(self.root, sem_snap)
        with self.assertRaises(PreExecutionAssertionError):
            validator.validate_plan_preconditions(plan)

if __name__ == "__main__":
    unittest.main()
