import unittest
from app import run_app

class TestApp(unittest.TestCase):
    def test_run_app(self):
        self.assertEqual(run_app(), 20)
