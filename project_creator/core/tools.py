import subprocess
import os
import shlex
import logging

# Set up audit logging
logging.basicConfig(filename="agent_audit.log", level=logging.INFO, format='%(asctime)s - %(message)s')

class ToolExecutor:
    def __init__(self, project_root):
        self.project_root = os.path.realpath(os.path.abspath(project_root))
        # Sandbox Constitution: Strictly Whitelisted Bases
        self.allowed_bases = {"pytest", "ruff", "black", "python3"}

    def execute(self, command):
        try:
            cmd_args = shlex.split(command)
        except ValueError as e:
            return {"error": f"Parse Error: {e}"}

        if not cmd_args: return {"error": "Empty command."}

        cmd_base = cmd_args[0]

        # 1. Base command verification
        if cmd_base not in self.allowed_bases:
            logging.warning(f"REJECTED: {command}")
            return {"error": f"Sandbox Rejection: '{cmd_base}' is restricted."}

        # 2. Forbidden pattern verification
        forbidden = {
            "sudo", "chmod", "chown", "env", ".env", "passwd", "shadow",
            "rm -rf /", "git", "pip", "sh", "bash", "curl", "wget", "eval", "exec"
        }
        for arg in cmd_args:
            if any(p in arg.lower() for p in forbidden):
                 logging.warning(f"REJECTED PATTERN: {command}")
                 return {"error": f"Constitution Violation: Forbidden pattern detected."}

        try:
            # 3. Clean environment and non-shell execution
            logging.info(f"EXECUTING: {command} in {self.project_root}")
            result = subprocess.run(
                cmd_args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
                shell=False,
                env={"PYTHONPATH": os.environ.get("PYTHONPATH", "")} # Minimal env
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
