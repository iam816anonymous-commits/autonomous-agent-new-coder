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

    async def execute_async(self, command, needs_approval=None):
        if needs_approval is None:
            if command.startswith("python3"): needs_approval = True

        if needs_approval:
            import uuid
            import asyncio
            from project_creator.server import state
            cmd_id = str(uuid.uuid4())
            state.pending_commands[cmd_id] = {"command": command, "status": "pending"}
            print(f"🛑 Security: Command requires human approval: {command}")

            start_wait = time.time()
            while time.time() - start_wait < 60:
                if state.pending_commands.get(cmd_id, {}).get('status') == 'approved':
                    del state.pending_commands[cmd_id]
                    break
                await asyncio.sleep(1)
            else:
                return {"error": "Security Rejection: Human approval timeout."}

        return self.execute(command)

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
            "rm -rf", "git", "pip", "sh", "bash", "curl", "wget", "eval", "exec",
            "systemctl", "docker", "ssh", "scp", "nc", "nmap"
        }

        # 3. High-Risk commands requiring approval
        high_risk = {"python3", "pytest", "ruff", "black"} # While allowed, we might want to flag specific usages
        for arg in cmd_args:
            if any(p in arg.lower() for p in forbidden):
                 logging.warning(f"REJECTED PATTERN: {command}")
                 return {"error": f"Constitution Violation: Forbidden pattern detected."}

        try:
            # 3. Clean environment and non-shell execution (with venv support)
            logging.info(f"EXECUTING: {command} in {self.project_root}")

            env = {"PYTHONPATH": os.environ.get("PYTHONPATH", "")}
            venv_bin = os.path.join(self.project_root, "venv", "bin")
            if os.path.exists(venv_bin):
                env["PATH"] = venv_bin + os.pathsep + os.environ.get("PATH", "")
                # Point to venv python if running python scripts
                if cmd_args[0] == "python3":
                    cmd_args[0] = os.path.join(venv_bin, "python3")

            result = subprocess.run(
                cmd_args,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30,
                shell=False,
                env=env
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {"error": str(e)}

    def ensure_venv(self):
        """Creates a virtual environment if it doesn't exist."""
        venv_path = os.path.join(self.project_root, "venv")
        if not os.path.exists(venv_path):
            print(f"📦 Creating Sandbox Venv in {self.project_root}...")
            subprocess.run(["python3", "-m", "venv", venv_path], check=True)
            # Install core validation tools into venv
            # In real scenario we might want to install requirements.txt too
            bin_path = os.path.join(venv_path, "bin", "pip")
            subprocess.run([bin_path, "install", "ruff", "black", "pytest"], capture_output=True)

    def run_lint(self, p): return self.execute(f"ruff check {p}")
    def run_format(self, p): return self.execute(f"black {p}")
    def run_tests(self): return self.execute("pytest")
