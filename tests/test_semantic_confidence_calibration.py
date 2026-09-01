import unittest
from repository.semantic.calibration import ConfidenceCalibrator
from repository.semantic.models import ConfidenceLevel

class TestSemanticConfidenceCalibration(unittest.TestCase):
    def test_calibration_score_computation(self):
        res1 = ConfidenceCalibrator.calculate_confidence("AST", is_unique=True)
        self.assertEqual(res1["confidence_level"], ConfidenceLevel.HIGH.value)

        res2 = ConfidenceCalibrator.calculate_confidence("AST", is_unique=True, has_dynamic_features=True)
        self.assertEqual(res2["confidence_level"], ConfidenceLevel.MEDIUM.value)

if __name__ == "__main__":
    unittest.main()
