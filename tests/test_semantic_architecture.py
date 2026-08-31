import unittest
from repository.models import RepositoryInfo
from repository.semantic.architecture import ArchitectureDetector
from repository.semantic.models import ArchitecturePattern

class TestSemanticArchitecture(unittest.TestCase):
    def test_architecture_detection_service_repo(self):
        info = RepositoryInfo(
            root=".",
            source_files=["controllers/user_controller.py", "services/user_service.py", "repositories/user_repo.py"]
        )
        res = ArchitectureDetector.detect_architecture(info)
        self.assertIn(ArchitecturePattern.SERVICE_REPOSITORY.value, res["patterns"])
        self.assertEqual(res["confidence"], "HIGH")

if __name__ == "__main__":
    unittest.main()
