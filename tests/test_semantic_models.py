import unittest
from repository.semantic.models import SemanticSymbol, SymbolKind, ConfidenceLevel
from repository.semantic.graph import SemanticRepositoryGraph

class TestSemanticModels(unittest.TestCase):
    def test_semantic_symbol_instantiation(self):
        sym = SemanticSymbol(
            symbol_id="mod:app.py:func",
            name="func",
            qualified_name="app.func",
            symbol_kind=SymbolKind.FUNCTION,
            language="Python",
            file_path="app.py"
        )
        self.assertEqual(sym.name, "func")
        self.assertEqual(sym.symbol_kind, SymbolKind.FUNCTION)

if __name__ == "__main__":
    unittest.main()
