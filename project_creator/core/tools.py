import subprocess
import os
import shlex

class ToolExecutor:
    def __init__(self, project_root):
        self.project_root = os.path.abspath(project_root)
        # Strict whitelist
        self.allowed_bases = {"pytest", "ruff", "black", "python3"}

    def execute(self, command):
        try:
            cmd_args = shlex.split(command)
        except ValueError as e:
            return {"error": f"Invalid command syntax: {e}"}

        if not cmd_args:
             return {"error": "Empty command."}

        cmd_base = cmd_args[0]

        # Security hardening: Deny shell escalation, credential edits, system edits
        # We block anything starting with 'git', 'pip', or contains 'sudo', 'env', etc.
        if cmd_base not in self.allowed_bases:
             return {"error": f"Permission Denied: Command '{cmd_base}' is restricted."}

        # Check for forbidden keywords in arguments
        forbidden = {"sudo", "chmod", "chown", "env", ".env", "passwd", "shadow"}
        for arg in cmd_args:
            if any(f in arg.lower() for f in forbidden):
                return {"error": f"Security Violation: Forbidden keyword detected in arguments."}

        try:
            # Execute without shell=True to prevent injection
            result = subprocess.run(
                cmd_args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
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
