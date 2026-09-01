import tempfile
import os
import unittest
from engine.change_planning.models import ChangeRequest, ChangeRequestType
from engine.change_planning.discovery import ChangeDiscoveryEngine
from repository.scan import RepositoryAnalyzer
from repository.semantic.snapshot import SemanticSnapshotter

class TestChangeDiscovery(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

        self.f1 = os.path.join(self.root, "auth.py")
        with open(self.f1, "w") as f:
            f.write("def login_user(username, password):\n    pass\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_discovery_engine_finds_login_symbol(self):
        repo_snap = RepositoryAnalyzer.analyze(self.root)
        sem_snap = SemanticSnapshotter.capture(repo_snap)

        req = ChangeRequest(
            request_id="REQ-DISC-1",
            user_intent="Update login_user authentication handler",
            request_type=ChangeRequestType.FEATURE,
            description="Update login_user"
        )

        disc_eng = ChangeDiscoveryEngine(sem_snap)
        res = disc_eng.discover_change_targets(req)

        self.assertTrue(res["sufficient_evidence"])
        self.assertIn("login_user", res["matched_symbols"])

if __name__ == "__main__":
    unittest.main()
