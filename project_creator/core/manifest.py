import yaml
import os
import time

class ProjectManifest:
    def __init__(self, project_root):
        self.path = os.path.join(project_root, "project.yaml")

    def create(self, goal, stack, files):
        data = {
            "project": {
                "id": f"proj_{int(time.time())}",
                "goal": goal,
                "status": "in_progress",
                "stack": stack,
                "files": files,
                "patches": {"pending": [], "approved": []},
                "validation": {"tests": "pending"},
                "approvals": [],
                "sessions": []
            }
        }
        with open(self.path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

    def update_field(self, key, value):
        if not os.path.exists(self.path): return
        with open(self.path, 'r') as f:
            data = yaml.safe_load(f)

        # Handle nested keys if needed, but simple for now
        data['project'][key] = value

        with open(self.path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

    def log_approval(self, file_path):
        if not os.path.exists(self.path): return
        with open(self.path, 'r') as f:
            data = yaml.safe_load(f)
        data['project']['approvals'].append(file_path)
        with open(self.path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                return yaml.safe_load(f)
        return None
