import os
import unittest
from engine.classifier.classifier import TaskClassifier
from engine.classifier.models import TaskType, TaskClassificationStatus
from repository.scan import RepositoryAnalyzer

FIXTURES_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "fixtures"))

class TestTaskClassifierPositives(unittest.TestCase):
    def setUp(self):
        self.classifier = TaskClassifier()

    def test_symbol_rename(self):
        res = self.classifier.classify("Rename calculate_total to calculate_invoice_total")
        self.assertEqual(res.task_type, TaskType.SYMBOL_RENAME)
        self.assertEqual(res.status, TaskClassificationStatus.SUPPORTED)
        self.assertEqual(res.extracted_parameters["old_name"], "calculate_total")
        self.assertEqual(res.extracted_parameters["new_name"], "calculate_invoice_total")

    def test_dependency_upgrade(self):
        res = self.classifier.classify("Upgrade FastAPI to version 0.120")
        self.assertEqual(res.task_type, TaskType.DEPENDENCY_UPGRADE)
        self.assertEqual(res.status, TaskClassificationStatus.SUPPORTED)
        self.assertEqual(res.extracted_parameters["package"], "FastAPI")
        self.assertEqual(res.extracted_parameters["target_version"], "0.120")

    def test_route_extension(self):
        res = self.classifier.classify("Add DELETE /users/:id")
        self.assertEqual(res.task_type, TaskType.ROUTE_EXTENSION)
        self.assertEqual(res.extracted_parameters["http_method"], "DELETE")
        self.assertEqual(res.extracted_parameters["route"], "/users/:id")

    def test_crud_extension(self):
        res = self.classifier.classify("Add CRUD for products")
        self.assertEqual(res.task_type, TaskType.CRUD_EXTENSION)
        self.assertEqual(res.extracted_parameters["resource"], "products")

    def test_file_move(self):
        res = self.classifier.classify("Move src/foo.py to src/utils/foo.py")
        self.assertEqual(res.task_type, TaskType.FILE_MOVE)
        self.assertEqual(res.extracted_parameters["source"], "src/foo.py")
        self.assertEqual(res.extracted_parameters["destination"], "src/utils/foo.py")

    def test_migration(self):
        res = self.classifier.classify("Convert CommonJS to ESM")
        self.assertEqual(res.task_type, TaskType.MIGRATION)
        self.assertEqual(res.extracted_parameters["from_framework"], "CommonJS")
        self.assertEqual(res.extracted_parameters["to_framework"], "ESM")

    def test_test_repair(self):
        res = self.classifier.classify("Fix failing pytest tests")
        self.assertEqual(res.task_type, TaskType.TEST_REPAIR)

    def test_code_formatting(self):
        res = self.classifier.classify("Format the project")
        self.assertEqual(res.task_type, TaskType.CODE_FORMATTING)

    def test_analysis_only(self):
        res = self.classifier.classify("Analyze the repository")
        self.assertEqual(res.task_type, TaskType.ANALYSIS_ONLY)

    def test_template_generation(self):
        res = self.classifier.classify("Create a FastAPI project template")
        self.assertEqual(res.task_type, TaskType.TEMPLATE_GENERATION)

    def test_documentation_update(self):
        res = self.classifier.classify("Update README")
        self.assertEqual(res.task_type, TaskType.DOCUMENTATION_UPDATE)


class TestTaskClassifierNegationAndQuestions(unittest.TestCase):
    def setUp(self):
        self.classifier = TaskClassifier()

    def test_negation(self):
        res1 = self.classifier.classify("Do not rename calculate_total")
        self.assertEqual(res1.status, TaskClassificationStatus.AMBIGUOUS)

        res2 = self.classifier.classify("Don't upgrade React")
        self.assertEqual(res2.status, TaskClassificationStatus.AMBIGUOUS)

    def test_informational_questions(self):
        res1 = self.classifier.classify("Explain how to rename calculate_total")
        self.assertEqual(res1.task_type, TaskType.ANALYSIS_ONLY)

        res2 = self.classifier.classify("Should we upgrade React?")
        self.assertEqual(res2.task_type, TaskType.ANALYSIS_ONLY)

        res3 = self.classifier.classify("Find out why React upgrade is failing")
        self.assertEqual(res3.task_type, TaskType.ANALYSIS_ONLY)


class TestTaskClassifierAmbiguousAndVague(unittest.TestCase):
    def setUp(self):
        self.classifier = TaskClassifier()

    def test_vague_prompts(self):
        vague_inputs = ["Fix this project", "Improve the code", "Make everything better", "Clean everything"]
        for inp in vague_inputs:
            res = self.classifier.classify(inp)
            self.assertEqual(res.status, TaskClassificationStatus.AMBIGUOUS)
            self.assertTrue(len(res.warnings) > 0)


class TestTaskClassifierComposite(unittest.TestCase):
    def setUp(self):
        self.classifier = TaskClassifier()

    def test_composite_request(self):
        res = self.classifier.classify("Upgrade React to 19 and rename calculate_total to calculate_invoice_total")
        self.assertEqual(res.task_type, TaskType.COMPOSITE_TASK)
        self.assertEqual(len(res.subtasks), 2)
        sub_types = [s.task_type for s in res.subtasks]
        self.assertIn(TaskType.DEPENDENCY_UPGRADE, sub_types)
        self.assertIn(TaskType.SYMBOL_RENAME, sub_types)


class TestTaskClassifierRepositoryAware(unittest.TestCase):
    def setUp(self):
        self.classifier = TaskClassifier()
        self.root = os.path.join(FIXTURES_DIR, "python_simple")
        self.snapshot = RepositoryAnalyzer.analyze(self.root)

    def test_repo_aware_rename_existing(self):
        # 'add' exists in python_simple
        res = self.classifier.classify("Rename add to sum_numbers", repo_snapshot=self.snapshot)
        self.assertEqual(res.task_type, TaskType.SYMBOL_RENAME)
        self.assertEqual(res.confidence, 0.95)
        self.assertTrue(any("Confirmed symbol 'add' exists" in e for e in res.evidence))

    def test_repo_aware_rename_missing(self):
        # 'non_existent_fn' does not exist
        res = self.classifier.classify("Rename non_existent_fn to new_fn", repo_snapshot=self.snapshot)
        self.assertEqual(res.task_type, TaskType.SYMBOL_RENAME)
        self.assertTrue(len(res.warnings) > 0)
        self.assertTrue(res.confidence < 0.90)


class TestDeterminismAndNoLLM(unittest.TestCase):
    def setUp(self):
        self.classifier = TaskClassifier()

    def test_deterministic_reproducibility(self):
        prompt = "Rename calculate_total to calculate_invoice_total"
        res1 = self.classifier.classify(prompt)
        res2 = self.classifier.classify(prompt)
        res3 = self.classifier.classify(prompt)

        self.assertEqual(res1, res2)
        self.assertEqual(res2, res3)

    def test_no_llm_acceptance(self):
        res = self.classifier.classify("Upgrade FastAPI to version 0.120")
        self.assertIsNotNone(res.task_type)
        self.assertIsNotNone(res.confidence)
        self.assertTrue(len(res.evidence) > 0)

if __name__ == "__main__":
    unittest.main()
