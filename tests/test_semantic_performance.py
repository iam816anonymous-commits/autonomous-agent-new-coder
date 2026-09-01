import tempfile
import os
import time
import unittest
from repository.scan import RepositoryAnalyzer
from repository.semantic.snapshot import SemanticSnapshotter

class TestSemanticPerformance(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

        # Create 10 source files
        for i in range(10):
            fpath = os.path.join(self.root, f"module_{i}.py")
            with open(fpath, "w") as f:
                f.write(f"def func_{i}():\n    return {i}\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_semantic_analysis_performance_benchmark(self):
        start_time = time.time()
        repo_snap = RepositoryAnalyzer.analyze(self.root)
        sem_snap = SemanticSnapshotter.capture(repo_snap)
        duration = time.time() - start_time

        self.assertTrue(duration < 2.0)  # Must complete in under 2.0s
        self.assertEqual(len(sem_snap.graph.symbols), 20) # 10 modules + 10 functions

if __name__ == "__main__":
    unittest.main()
