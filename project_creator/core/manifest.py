import yaml
import os

class ProjectManifest:
    def __init__(self, project_root):
        self.path = os.path.join(project_root, "project.yaml")

    def create(self, goal, stack, files, deps=None, tests=None):
        data = {
            "goal": goal,
            "stack": stack,
            "files": files,
            "deps": deps or [],
            "tests": tests or [],
            "status": "in_progress"
        }
        with open(self.path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

    def update_status(self, status):
        if not os.path.exists(self.path): return
        with open(self.path, 'r') as f:
            data = yaml.safe_load(f)
        data['status'] = status
        with open(self.path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                return yaml.safe_load(f)
        return None
