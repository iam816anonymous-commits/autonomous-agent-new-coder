import unittest
from fastapi.testclient import TestClient
import os
import sys

# Ensure project_root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from project_creator.server import app

client = TestClient(app)

class TestServer(unittest.TestCase):
    def test_init(self):
        # We need to mock the agents to avoid API calls
        response = client.post("/initialize", json={"goal": "test", "project_name": "test_proj"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "initialized")

if __name__ == '__main__':
    unittest.main()
