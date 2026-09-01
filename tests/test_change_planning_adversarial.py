import tempfile
import os
import unittest
from engine.change_planning.models import ChangeRequest, ChangeRequestType
from engine.change_planning.discovery import ChangeDiscoveryEngine
from repository.scan import RepositoryAnalyzer
from repository.semantic.snapshot import SemanticSnapshotter

class TestChangePlanningAdversarial(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_misleading_and_duplicate_symbol_discovery(self):
        # Create multiple files with duplicate class names
        f1 = os.path.join(self.root, "auth_v1.py")
        f2 = os.path.join(self.root, "auth_v2.py")

        with open(f1, "w") as f:
            f.write("class AuthHandler:\n    pass\n")
        with open(f2, "w") as f:
            f.write("class AuthHandler:\n    pass\n")

        repo_snap = RepositoryAnalyzer.analyze(self.root)
        sem_snap = SemanticSnapshotter.capture(repo_snap)

        req = ChangeRequest("REQ-ADV-1", "Update AuthHandler", ChangeRequestType.REFACTOR, "Refactor")
        disc_eng = ChangeDiscoveryEngine(sem_snap)
        res = disc_eng.discover_change_targets(req)

        self.assertEqual(res["confidence"].value, "MEDIUM")
        self.assertEqual(len(res["target_files"]), 2)

if __name__ == "__main__":
    unittest.main()
