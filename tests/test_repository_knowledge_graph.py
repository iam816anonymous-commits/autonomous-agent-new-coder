import os
import unittest
from repository.scanner import RepositoryScanner
from repository.symbols import SymbolIndexer
from repository.dependency_graph import DependencyGraphBuilder
from repository.impact_analysis import ImpactAnalyzer
from repository.scan import RepositoryAnalyzer
from repository.models import BlastRadiusLevel

FIXTURES_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__), "fixtures"))

class TestRepositoryScanner(unittest.TestCase):
    def test_python_simple_scan(self):
        root = os.path.join(FIXTURES_DIR, "python_simple")
        scanner = RepositoryScanner(root)
        info, file_map = scanner.scan()

        self.assertIn("Python", info.languages)
        self.assertIn("FastAPI", info.frameworks)
        self.assertIn("pip", info.package_managers)
        self.assertIn("app.py", info.entry_points)
        self.assertIn("tests/test_app.py", info.test_files)
        self.assertIn("utils.py", info.source_files)

    def test_typescript_simple_scan(self):
        root = os.path.join(FIXTURES_DIR, "typescript_simple")
        scanner = RepositoryScanner(root)
        info, file_map = scanner.scan()

        self.assertIn("TypeScript", info.languages)
        self.assertIn("Express", info.frameworks)
        self.assertIn("React", info.frameworks)
        self.assertIn("npm", info.package_managers)
        self.assertIn("index.ts", info.entry_points)
        self.assertIn("tests/user.test.ts", info.test_files)

    def test_path_safety(self):
        root = os.path.join(FIXTURES_DIR, "python_simple")
        scanner = RepositoryScanner(root)
        self.assertFalse(scanner._is_safe_path("../../../etc/passwd"))


class TestSymbolIndexer(unittest.TestCase):
    def test_python_symbols(self):
        root = os.path.join(FIXTURES_DIR, "python_simple")
        indexer = SymbolIndexer(root)
        indexer.index_repository(["app.py", "utils.py"])

        add_syms = indexer.find_definitions("add")
        self.assertTrue(len(add_syms) >= 1)
        self.assertEqual(add_syms[0].file_path, "utils.py")

        run_syms = indexer.find_definitions("run_app")
        self.assertTrue(len(run_syms) >= 1)
        self.assertEqual(run_syms[0].file_path, "app.py")

        callers_add = indexer.get_callers("add")
        self.assertIn("app.py", callers_add)

    def test_typescript_symbols(self):
        root = os.path.join(FIXTURES_DIR, "typescript_simple")
        indexer = SymbolIndexer(root)
        indexer.index_repository(["index.ts", "services/user.ts"])

        user_class = indexer.find_definitions("UserService")
        self.assertTrue(len(user_class) >= 1)
        self.assertEqual(user_class[0].file_path, "services/user.ts")


class TestDependencyGraph(unittest.TestCase):
    def test_python_dependencies(self):
        root = os.path.join(FIXTURES_DIR, "python_simple")
        dep_builder = DependencyGraphBuilder(root)
        graph = dep_builder.build_graph(["app.py", "utils.py", "tests/test_app.py"])

        self.assertIn("utils.py", dep_builder.get_dependencies("app.py"))
        self.assertIn("app.py", dep_builder.get_dependents("utils.py"))
        self.assertFalse(dep_builder.has_cycle())

        top_order = dep_builder.topological_order()
        self.assertTrue(top_order.index("utils.py") < top_order.index("app.py"))

    def test_circular_dependencies(self):
        root = os.path.join(FIXTURES_DIR, "python_circular")
        dep_builder = DependencyGraphBuilder(root)
        graph = dep_builder.build_graph(["module_a.py", "module_b.py", "module_c.py"])

        self.assertTrue(dep_builder.has_cycle())
        cycles = dep_builder.detect_cycles()
        self.assertTrue(len(cycles) >= 1)


class TestImpactAnalyzer(unittest.TestCase):
    def test_impact_analysis(self):
        root = os.path.join(FIXTURES_DIR, "python_simple")
        snapshot = RepositoryAnalyzer.analyze(root)
        report = snapshot.analyze_file_impact("utils.py")

        self.assertIn("app.py", report.direct_dependents)
        self.assertIn("tests/test_app.py", report.related_tests)
        self.assertIn("add", report.related_symbols)
        self.assertIn(report.blast_radius, [BlastRadiusLevel.LOW, BlastRadiusLevel.MEDIUM])


class TestDeterminismAndAcceptance(unittest.TestCase):
    def test_deterministic_reproducibility(self):
        root = os.path.join(FIXTURES_DIR, "python_simple")
        snap1 = RepositoryAnalyzer.analyze(root).to_dict()
        snap2 = RepositoryAnalyzer.analyze(root).to_dict()
        snap3 = RepositoryAnalyzer.analyze(root).to_dict()

        self.assertEqual(snap1, snap2)
        self.assertEqual(snap2, snap3)

    def test_no_llm_acceptance(self):
        # Full Phase A pipeline runs without LLM, network or API keys
        root = os.path.join(FIXTURES_DIR, "python_simple")
        snapshot = RepositoryAnalyzer.analyze(root)

        self.assertIsNotNone(snapshot.info)
        self.assertIsNotNone(snapshot.symbols)
        self.assertIsNotNone(snapshot.graph)
        self.assertIsNotNone(snapshot.impact_analyzer)

if __name__ == "__main__":
    unittest.main()
