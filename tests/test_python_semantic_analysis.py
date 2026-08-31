import tempfile
import os
import unittest
from repository.semantic.graph import SemanticRepositoryGraph
from repository.semantic.python_analyzer import PythonSemanticAnalyzer
from repository.semantic.call_graph import ConservativeCallGraph
from repository.semantic.models import SymbolKind

class TestPythonSemanticAnalyzer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = self.temp_dir.name

        self.app_path = os.path.join(self.root, "app.py")
        with open(self.app_path, "w") as f:
            f.write("def helper():\n    return 42\n\ndef main():\n    return helper()\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_python_ast_symbol_and_call_extraction(self):
        graph = SemanticRepositoryGraph()
        analyzer = PythonSemanticAnalyzer(self.root, graph)
        analyzer.analyze_file("app.py")

        syms = graph.find_symbols("helper")
        self.assertEqual(len(syms), 1)
        self.assertEqual(syms[0].symbol_kind, SymbolKind.FUNCTION)

        call_graph = ConservativeCallGraph(graph)
        callers = call_graph.get_callers("helper")
        self.assertEqual(len(callers), 1)

if __name__ == "__main__":
    unittest.main()
