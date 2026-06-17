class ExecutionCoordinator:
    """
    Handles the physical execution of tools and tests.
    """

    def __init__(self, tool_executor, test_executor):
        self.tools = tool_executor
        self.tests = test_executor

    def run_validation(self, path: str):
        print(f"🔍 [EXEC] Validating {path}...")
        return self.tools.run_lint(path)

    def run_test_suite(self):
        print("🧪 [EXEC] Running project test suite...")
        return self.tests.run_tests()
