import unittest
from repository.semantic.models import SemanticSymbol, SymbolKind, ConfidenceLevel
from repository.semantic.trust.models import SemanticTrustLevel
from repository.semantic.trust.trust_levels import SemanticTrustEvaluator

class TestSemanticTrustModels(unittest.TestCase):
    def test_trust_level_evaluation(self):
        sym = SemanticSymbol("s1", "calc", "app.calc", SymbolKind.FUNCTION, "Python", "app.py", confidence=ConfidenceLevel.HIGH)
        res = SemanticTrustEvaluator.evaluate_symbol_trust(sym)
        self.assertEqual(res.trust_level, SemanticTrustLevel.HIGH_CONFIDENCE)
        self.assertTrue(res.allows_autonomous_modification)

if __name__ == "__main__":
    unittest.main()
