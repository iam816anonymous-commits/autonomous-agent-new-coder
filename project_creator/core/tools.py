import subprocess
import os
import shlex

class ToolExecutor:
    def __init__(self, project_root):
        self.project_root = os.path.abspath(project_root)
        # Sandbox Constitution: Strictly whitelisted commands
        self.allowed_bases = {"pytest", "ruff", "black", "python3"}

    def execute(self, command):
        try:
            cmd_args = shlex.split(command)
        except ValueError as e:
            return {"error": f"Invalid syntax: {e}"}

        if not cmd_args: return {"error": "Empty command."}

        cmd_base = cmd_args[0]

        # Hardened Reject: Escalation, System, Credentials, Recursive
        if cmd_base not in self.allowed_bases:
            return {"error": f"Sandbox Rejection: Command '{cmd_base}' is restricted."}

        # Forbidden patterns for credentials/system edits/shell escalation
        forbidden = {
            "sudo", "chmod", "chown", "env", ".env", "passwd", "shadow",
            "rm -rf /", "git", "pip", "sh", "bash", "curl", "wget"
        }

        full_cmd_str = " ".join(cmd_args).lower()
        for pattern in forbidden:
            if pattern in full_cmd_str:
                return {"error": f"Constitution Violation: Forbidden pattern detected."}

        try:
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

    def run_lint(self, path): return self.execute(f"ruff check {path}")
    def run_format(self, path): return self.execute(f"black {path}")
    def run_tests(self): return self.execute("pytest")
