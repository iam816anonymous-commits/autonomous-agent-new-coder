import subprocess
import os

class ToolExecutor:
    def __init__(self, project_root):
        self.project_root = os.path.abspath(project_root)
        self.allowed_commands = ["pytest", "ruff", "black", "alembic", "git status", "pip install", "python"]

    def execute(self, command):
        # Basic safety check
        cmd_base = command.split()[0]
        if cmd_base not in self.allowed_commands and not command.startswith("python "):
             return f"Error: Command '{cmd_base}' is not in the allowed list."

        try:
            # Execute command within project root
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {"error": str(e)}

    def run_lint(self, file_path):
        return self.execute(f"ruff check {file_path}")

    def run_format(self, file_path):
        return self.execute(f"black {file_path}")

    def run_tests(self):
        return self.execute("pytest")
