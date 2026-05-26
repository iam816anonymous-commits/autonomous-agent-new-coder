import yaml
import os

class ProjectManifest:
    def __init__(self, project_root):
        self.path = os.path.join(project_root, "project.yaml")

    def create(self, name, stack, files):
        data = {
            "project": {
                "name": name,
                "stack": stack,
                "status": "in_progress",
                "files": files,
                "repairs": "none"
            }
        }
        with open(self.path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

    def update_status(self, status):
        if not os.path.exists(self.path): return
        with open(self.path, 'r') as f:
            data = yaml.safe_load(f)
        data['project']['status'] = status
        with open(self.path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

    def update_repairs(self, repair_status):
        if not os.path.exists(self.path): return
        with open(self.path, 'r') as f:
            data = yaml.safe_load(f)
        data['project']['repairs'] = repair_status
        with open(self.path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                return yaml.safe_load(f)
        return None
