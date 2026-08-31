import tempfile
import os
import unittest
from repository.scan import RepositoryAnalyzer
from repository.semantic.snapshot import SemanticSnapshotter
from repository.semantic.queries import SemanticQueryEngine

class TestSemanticImpactAndSnapshot(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

        self.file1 = os.path.join(self.root, "service.py")
        with open(self.file1, "w") as f:
            f.write("class UserService:\n    def get_user(self):\n        pass\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_semantic_snapshot_and_query_engine(self):
        repo_snap = RepositoryAnalyzer.analyze(self.root)
        sem_snap = SemanticSnapshotter.capture(repo_snap)

        self.assertIsNotNone(sem_snap.repository_fingerprint)
        self.assertTrue(len(sem_snap.graph.symbols) >= 1)

        query_eng = SemanticQueryEngine(sem_snap.graph)
        impl_path = query_eng.implementation_path("UserService")
        self.assertIn("UserService", impl_path["matched_symbols"])

if __name__ == "__main__":
    unittest.main()
