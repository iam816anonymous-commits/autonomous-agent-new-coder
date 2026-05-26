import subprocess
import os
import shlex

class ToolExecutor:
    def __init__(self, project_root):
        self.project_root = os.path.abspath(project_root)
        # Sandbox Constitution: ALLOW list
        self.allowed_bases = {"pytest", "ruff", "black", "python3"}

    def execute(self, command):
        try:
            cmd_args = shlex.split(command)
        except ValueError as e:
            return {"error": f"Syntax Error: {e}"}

        if not cmd_args: return {"error": "Empty command."}

        cmd_base = cmd_args[0]

        # Sandbox Constitution: DENY list & Hard Checks
        if cmd_base not in self.allowed_bases:
            return {"error": f"Sandbox Rejection: '{cmd_base}' is restricted."}

        forbidden_patterns = {
            "sudo", "chmod", "chown", "env", ".env", "passwd", "shadow",
            "rm -rf /", "git", "pip", "bash", "sh", "curl", "wget"
        }

        full_cmd = " ".join(cmd_args).lower()
        for pattern in forbidden_patterns:
            if pattern in full_cmd:
                 return {"error": f"Constitution Violation: '{pattern}' is forbidden."}

        try:
            # Final block for recursive execution attempts or shell escalation
            result = subprocess.run(
                cmd_args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
                shell=False # Immutable: never use shell=True
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
