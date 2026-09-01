import tempfile
import os
import time
import unittest
from engine.change_planning.models import ChangeRequest, ChangeRequestType
from engine.change_planning.discovery import ChangeDiscoveryEngine
from repository.scan import RepositoryAnalyzer
from repository.semantic.snapshot import SemanticSnapshotter

class TestChangePlanningPerformance(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

        for i in range(15):
            fpath = os.path.join(self.root, f"service_{i}.py")
            with open(fpath, "w") as f:
                f.write(f"def process_data_{i}():\n    pass\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_change_planning_performance_benchmark(self):
        start_time = time.time()
        repo_snap = RepositoryAnalyzer.analyze(self.root)
        sem_snap = SemanticSnapshotter.capture(repo_snap)

        req = ChangeRequest("REQ-PERF-1", "Update process_data_5", ChangeRequestType.REFACTOR, "Refactor")
        disc_eng = ChangeDiscoveryEngine(sem_snap)
        res = disc_eng.discover_change_targets(req)

        duration = time.time() - start_time
        self.assertTrue(duration < 2.0)
        self.assertIn("process_data_5", res["matched_symbols"])

if __name__ == "__main__":
    unittest.main()
