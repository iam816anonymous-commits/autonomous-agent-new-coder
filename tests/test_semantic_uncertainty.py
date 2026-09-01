import unittest
from repository.semantic.graph import SemanticRepositoryGraph
from repository.semantic.models import SemanticSymbol, SymbolKind, SemanticRelation, SemanticRelationType, Evidence, ConfidenceLevel
from repository.semantic.uncertainty import UncertaintyPropagator

class TestSemanticUncertainty(unittest.TestCase):
    def test_uncertainty_propagates_to_callers(self):
        graph = SemanticRepositoryGraph()
        # s1 calls s2. s2 has LOW confidence.
        s1 = SemanticSymbol("s1", "main", "app.main", SymbolKind.FUNCTION, "Python", "app.py", confidence=ConfidenceLevel.HIGH)
        s2 = SemanticSymbol("s2", "helper", "app.helper", SymbolKind.FUNCTION, "Python", "app.py", confidence=ConfidenceLevel.LOW)

        graph.add_symbol(s1)
        graph.add_symbol(s2)

        rel = SemanticRelation(
            source_symbol_id="s1",
            target_symbol_id="s2",
            relation_type=SemanticRelationType.CALLS,
            evidence=Evidence("app.py", 10),
            confidence=ConfidenceLevel.HIGH
        )
        graph.add_relation(rel)

        degraded = UncertaintyPropagator.propagate_uncertainty(graph)
        self.assertTrue(degraded >= 1)
        self.assertEqual(s1.confidence, ConfidenceLevel.MEDIUM)

if __name__ == "__main__":
    unittest.main()
