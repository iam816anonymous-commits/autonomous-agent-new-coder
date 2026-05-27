import yaml
import os
import time

class ProjectManifest:
    def __init__(self, project_root):
        self.path = os.path.join(project_root, "project.yaml")

    def create(self, goal, stack, files):
        # Infer modules from paths (e.g. backend/main.py -> backend)
        modules = {}
        for f in files:
            parts = f.split('/')
            m = parts[0] if len(parts) > 1 else "root"
            if m not in modules: modules[m] = []
            modules[m].append(f)

        data = {
            "project": {
                "id": f"p_{int(time.time())}",
                "goal": goal,
                "stack": stack,
                "status": "active",
                "modules": modules,
                "files": files,
                "approvals": [],
                "validation": {"tests": "pending"}
            }
        }
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

    def add_approval(self, path):
        if not os.path.exists(self.path): return
        with open(self.path, 'r') as f:
            data = yaml.safe_load(f)
        if path not in data['project']['approvals']:
            data['project']['approvals'].append(path)
        with open(self.path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

    def update_field(self, key, value):
        if not os.path.exists(self.path): return
        with open(self.path, 'r') as f:
            data = yaml.safe_load(f)
        data['project'][key] = value
        with open(self.path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                return yaml.safe_load(f)
        return None
