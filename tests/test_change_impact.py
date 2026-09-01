import tempfile
import os
import unittest
from engine.change_planning.models import ChangeRequest, ChangeRequestType
from engine.change_planning.impact import ChangeImpactAnalyzer
from repository.scan import RepositoryAnalyzer
from repository.semantic.snapshot import SemanticSnapshotter

class TestChangeImpact(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

        self.f1 = os.path.join(self.root, "api_routes.py")
        with open(self.f1, "w") as f:
            f.write("def handle_request():\n    pass\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_change_impact_analyzer_detects_api_boundary(self):
        repo_snap = RepositoryAnalyzer.analyze(self.root)
        sem_snap = SemanticSnapshotter.capture(repo_snap)

        req = ChangeRequest("REQ-IMP-1", "Update handle_request", ChangeRequestType.REFACTOR, "Refactor")
        impact_eng = ChangeImpactAnalyzer(sem_snap)
        res = impact_eng.analyze_change_impact(req, ["handle_request"])

        self.assertIn("API_LAYER", res["architectural_boundaries_crossed"])

if __name__ == "__main__":
    unittest.main()
