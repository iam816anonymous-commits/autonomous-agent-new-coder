import unittest
from repository.semantic.python_dynamic import PythonDynamicDetector

class TestPythonDynamicDetection(unittest.TestCase):
    def test_dynamic_detector_catches_getattr_and_star_import(self):
        code = "from os import *\nx = getattr(obj, 'attr')\neval('1 + 1')\n"
        findings = PythonDynamicDetector.detect_dynamic_constructs(code, "test.py")

        types = [f["type"] for f in findings]
        self.assertIn("STAR_IMPORT", types)
        self.assertIn("DYNAMIC_FUNCTION_CALL", types)

if __name__ == "__main__":
    unittest.main()
