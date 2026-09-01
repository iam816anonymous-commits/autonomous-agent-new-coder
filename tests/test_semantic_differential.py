import tempfile
import os
import unittest
from repository.scan import RepositoryAnalyzer
from repository.semantic.snapshot import SemanticSnapshotter
from repository.semantic.differential import DifferentialSemanticAnalyzer

class TestSemanticDifferential(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

        self.f1 = os.path.join(self.root, "app.py")
        with open(self.f1, "w") as f:
            f.write("def foo():\n    pass\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_differential_analysis_detects_added_symbol(self):
        repo_snap1 = RepositoryAnalyzer.analyze(self.root)
        snap1 = SemanticSnapshotter.capture(repo_snap1)

        # Add a new symbol
        with open(self.f1, "a") as f:
            f.write("\ndef bar():\n    pass\n")

        repo_snap2 = RepositoryAnalyzer.analyze(self.root)
        snap2 = SemanticSnapshotter.capture(repo_snap2)

        diff = DifferentialSemanticAnalyzer.compare_snapshots(snap1, snap2)
        self.assertTrue(len(diff["added_symbols"]) >= 1)

if __name__ == "__main__":
    unittest.main()
