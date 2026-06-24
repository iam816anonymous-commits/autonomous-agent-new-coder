import json
import os


class SessionManager:
    def __init__(self, project_root):
        self.project_root = os.path.abspath(project_root)
        self.session_file = os.path.join(self.project_root, ".agent_session.json")

    def save_session(self, blueprint, generated_files, repairs, approvals):
        data = {
            "blueprint": blueprint,
            "generated_files": generated_files,
            "repairs": repairs,
            "approvals": approvals,
        }
        os.makedirs(self.project_root, exist_ok=True)
        with open(self.session_file, "w") as f:
            json.dump(data, f, indent=2)

    def load_session(self):
        if os.path.exists(self.session_file):
            with open(self.session_file, "r") as f:
                return json.load(f)
        return None
