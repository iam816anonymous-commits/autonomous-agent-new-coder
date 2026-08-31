import unittest
from repository.semantic.models import SemanticSymbol, SymbolKind, SemanticRelation, SemanticRelationType, Evidence
from repository.semantic.graph import SemanticRepositoryGraph
from repository.semantic.resolver import SemanticResolver

class TestSemanticGraphAndResolver(unittest.TestCase):
    def setUp(self):
        self.graph = SemanticRepositoryGraph()
        self.sym1 = SemanticSymbol("s1", "calc", "app.calc", SymbolKind.FUNCTION, "Python", "app.py")
        self.sym2 = SemanticSymbol("s2", "calc", "utils.calc", SymbolKind.FUNCTION, "Python", "utils.py")
        self.graph.add_symbol(self.sym1)
        self.graph.add_symbol(self.sym2)

    def test_find_symbols_and_ambiguity(self):
        syms = self.graph.find_symbols("calc")
        self.assertEqual(len(syms), 2)

        resolver = SemanticResolver(self.graph)
        res_ambiguous = resolver.resolve_definition("calc")
        self.assertEqual(res_ambiguous["status"], "AMBIGUOUS")

        res_file_context = resolver.resolve_definition("calc", context_file="app.py")
        self.assertEqual(res_file_context["status"], "RESOLVED")
        self.assertEqual(res_file_context["symbol"].symbol_id, "s1")

if __name__ == "__main__":
    unittest.main()
