import subprocess
import os
import shlex

class ToolExecutor:
    def __init__(self, project_root):
        self.project_root = os.path.abspath(project_root)
        # List of base commands allowed
        self.allowed_bases = {"pytest", "ruff", "black", "alembic", "git", "pip", "python", "python3"}

    def execute(self, command):
        # Use shlex to safely split the command string
        try:
            cmd_args = shlex.split(command)
        except ValueError as e:
            return {"error": f"Invalid command syntax: {e}"}

        if not cmd_args:
             return {"error": "Empty command."}

        cmd_base = cmd_args[0]
        if cmd_base not in self.allowed_bases:
             return {"error": f"Error: Command '{cmd_base}' is not in the allowed list."}

        try:
            # Execute command without shell=True to prevent injection
            result = subprocess.run(
                cmd_args,
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
