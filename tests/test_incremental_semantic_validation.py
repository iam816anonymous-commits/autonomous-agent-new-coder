import tempfile
import os
import unittest
from repository.scan import RepositoryAnalyzer
from repository.semantic.snapshot import SemanticSnapshotter
from repository.semantic.incremental_validator import IncrementalSemanticValidator

class TestIncrementalSemanticValidation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

        self.f1 = os.path.join(self.root, "mod.py")
        with open(self.f1, "w") as f:
            f.write("def func():\n    pass\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_incremental_validation_match(self):
        repo_snap = RepositoryAnalyzer.analyze(self.root)
        sem_snap = SemanticSnapshotter.capture(repo_snap)

        val_res = IncrementalSemanticValidator.validate_incremental_update(sem_snap, repo_snap, ["mod.py"])
        self.assertEqual(val_res["status"], "INCREMENTAL_MATCH")

if __name__ == "__main__":
    unittest.main()
