import tempfile
import os
import unittest
from engine.change_planning.models import ChangeRequest, ChangeRequestType, ChangePlan, ChangeStep
from engine.change_planning.outcome import ChangeOutcomeAnalyzer
from repository.scan import RepositoryAnalyzer
from repository.semantic.snapshot import SemanticSnapshotter

class TestChangeOutcomeAnalyzer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

        self.f1 = os.path.join(self.root, "calc.py")
        with open(self.f1, "w") as f:
            f.write("def foo():\n    pass\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_outcome_analyzer_compares_snapshots(self):
        repo_snap1 = RepositoryAnalyzer.analyze(self.root)
        snap1 = SemanticSnapshotter.capture(repo_snap1)

        # Modify workspace
        with open(self.f1, "a") as f:
            f.write("\ndef bar():\n    pass\n")

        repo_snap2 = RepositoryAnalyzer.analyze(self.root)
        snap2 = SemanticSnapshotter.capture(repo_snap2)

        req = ChangeRequest("r1", "intent", ChangeRequestType.FEATURE, "desc")
        step = ChangeStep("s1", "desc", target_files=["calc.py"], target_symbols=["mod:calc.py:foo"])
        plan = ChangePlan("p1", req, steps=[step])

        outcome = ChangeOutcomeAnalyzer.compare_expected_vs_actual(plan, snap1, snap2)
        self.assertIn(outcome.match_status, ["MATCH", "UNEXPECTED_CHANGE"])

if __name__ == "__main__":
    unittest.main()
