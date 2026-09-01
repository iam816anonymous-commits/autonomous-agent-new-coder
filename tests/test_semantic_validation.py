import unittest
from repository.semantic.models import SemanticSymbol, SymbolKind
from repository.semantic.graph import SemanticRepositoryGraph
from repository.semantic.validation.validator import SemanticGraphValidator
from repository.semantic.validation.models import ValidationStatus

class TestSemanticValidation(unittest.TestCase):
    def test_semantic_graph_validator_detects_duplicates(self):
        graph = SemanticRepositoryGraph()
        sym1 = SemanticSymbol("s1", "add", "app.add", SymbolKind.FUNCTION, "Python", "app.py")
        sym2 = SemanticSymbol("s2", "add", "app.add", SymbolKind.FUNCTION, "Python", "app.py")
        graph.add_symbol(sym1)
        graph.add_symbol(sym2)

        validator = SemanticGraphValidator(graph)
        res = validator.validate()
        self.assertEqual(res.status, ValidationStatus.PARTIALLY_VALID)
        self.assertEqual(res.duplicate_symbol_count, 1)

if __name__ == "__main__":
    unittest.main()
