import tempfile
import os
import unittest
from repository.scan import RepositoryAnalyzer
from repository.semantic.snapshot import SemanticSnapshotter
from repository.semantic.python_dynamic import PythonDynamicDetector
from repository.semantic.validation.validator import SemanticGraphValidator

class TestSemanticAdversarialCases(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_unparsable_and_dynamic_python_files(self):
        # 1. Unparsable syntax file
        broken_file = os.path.join(self.root, "broken.py")
        with open(broken_file, "w") as f:
            f.write("def broken_syntax(a, b syntax_error_here\n")

        # 2. Dynamic file
        dynamic_file = os.path.join(self.root, "dynamic.py")
        with open(dynamic_file, "w") as f:
            f.write("from os import *\nx = getattr(obj, 'attr')\n")

        repo_snap = RepositoryAnalyzer.analyze(self.root)
        sem_snap = SemanticSnapshotter.capture(repo_snap)

        validator = SemanticGraphValidator(sem_snap.graph)
        val_res = validator.validate()

        findings = PythonDynamicDetector.detect_dynamic_constructs("from os import *\nx = getattr(obj, 'attr')", "dynamic.py")
        self.assertTrue(len(findings) >= 2)

if __name__ == "__main__":
    unittest.main()
