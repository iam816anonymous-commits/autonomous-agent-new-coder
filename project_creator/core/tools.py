import subprocess
import os
import shlex

class ToolExecutor:
    def __init__(self, project_root):
        self.project_root = os.path.abspath(project_root)
        # Final Sandbox Constitution ALLOW-list
        self.allowed_bases = {"pytest", "ruff", "black", "python3"}

    def execute(self, command):
        try:
            cmd_args = shlex.split(command)
        except ValueError as e:
            return {"error": f"Parse Error: {e}"}

        if not cmd_args: return {"error": "Empty command."}

        cmd_base = cmd_args[0]

        # 1. Deny Shell Escalation & Recursive Execution
        if cmd_base not in self.allowed_bases:
            return {"error": f"Sandbox Rejection: '{cmd_base}' is restricted."}

        # 2. Deny Credential/System Mutation Patterns
        forbidden_patterns = {
            "sudo", "chmod", "chown", "env", ".env", "passwd", "shadow",
            "rm -rf /", "git", "pip", "sh", "bash", "curl", "wget", "eval", "exec"
        }

        cmd_str = " ".join(cmd_args).lower()
        for p in forbidden_patterns:
            if p in cmd_str:
                return {"error": f"Constitution Violation: '{p}' is forbidden."}

        try:
            # 3. Block System Mutation (Immutable shell=False)
            result = subprocess.run(
                cmd_args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
                shell=False
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {"error": str(e)}

    def run_lint(self, p): return self.execute(f"ruff check {p}")
    def run_format(self, p): return self.execute(f"black {p}")
    def run_tests(self): return self.execute("pytest")
