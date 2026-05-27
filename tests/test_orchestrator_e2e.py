import unittest
import os
import shutil
from unittest.mock import MagicMock
from project_creator.core.orchestrator import Orchestrator
from project_creator.core.storage import Storage

class TestOrchestratorE2E(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_e2e_project"
        if os.path.exists(self.test_dir): shutil.rmtree(self.test_dir)
        self.storage = Storage(self.test_dir)

    def test_apply_logic(self):
        # Mock agents
        agents = {
            'planner': MagicMock(),
            'coder': MagicMock(),
            'critique': MagicMock(),
            'repair': MagicMock()
        }
        orch = Orchestrator(None, agents, self.storage, None, MagicMock(), MagicMock())

        path = "test.py"
        content = "print('hello')"
        success = orch.apply(path, content)

        self.assertTrue(success)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, path)))

    def tearDown(self):
        if os.path.exists(self.test_dir): shutil.rmtree(self.test_dir)

if __name__ == '__main__':
    unittest.main()
