import os

from .tools import ToolExecutor


class TestExecutor:
    """
    Auto-detects and executes tests, classifying failures.
    """

    def __init__(self, project_root):
        self.project_root = project_root
        self.tools = ToolExecutor(project_root)

    def detect_test_framework(self):
        """Identifies the appropriate test framework."""
        if os.path.exists(
            os.path.join(self.project_root, "pytest.ini")
        ) or os.path.exists(os.path.join(self.project_root, "conftest.py")):
            return "pytest"
        if os.path.exists(os.path.join(self.project_root, "package.json")):
            return "npm test"
        if os.path.exists(os.path.join(self.project_root, "Cargo.toml")):
            return "cargo test"
        return "pytest"  # Default for Python projects

    def run_tests(self):
        framework = self.detect_test_framework()
        print(f"🧪 Running tests with {framework}...")

        if framework == "pytest":
            res = self.tools.run_tests()
        else:
            # For non-whitelisted bases in ToolExecutor, we might need to adjust ToolExecutor
            # or use subprocess directly if sandbox allows.
            res = self.tools.execute(framework)

        return res

    def classify_failure(self, stderr):
        """Categorizes test failure for the repair agent."""
        if "ModuleNotFoundError" in stderr or "ImportError" in stderr:
            return "IMPORT"
        if "SyntaxError" in stderr:
            return "SYNTAX"
        if "AssertionError" in stderr:
            return "LOGIC"
        if "TypeError" in stderr:
            return "TYPE"
        return "RUNTIME"

    def generate_repair_context(self, res):
        """Builds context for the repair agent."""
        return {
            "exit_code": res.get("returncode"),
            "stdout": res.get("stdout", ""),
            "stderr": res.get("stderr", ""),
            "failure_type": self.classify_failure(
                res.get("stderr", "") + res.get("stdout", "")
            ),
        }
