import yaml
import os

class ProjectManifest:
    def __init__(self, project_root):
        self.path = os.path.join(project_root, "project.yaml")

    def create(self, name, stack, generated_files):
        data = {
            "project": {
                "name": name,
                "status": "in_progress",
                "stack": {
                    "backend": stack.get("backend", "unknown"),
                    "frontend": stack.get("frontend", "unknown")
                },
                "files": {
                    "generated": generated_files
                },
                "patches": {
                    "pending": [],
                    "approved": []
                },
                "validation": {
                    "tests": "pending"
                }
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

    def add_patch(self, patch_file, approved=False):
        if not os.path.exists(self.path): return
        with open(self.path, 'r') as f:
            data = yaml.safe_load(f)
        key = 'approved' if approved else 'pending'
        data['project']['patches'][key].append(patch_file)
        with open(self.path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

    def update_validation(self, tests_status):
        if not os.path.exists(self.path): return
        with open(self.path, 'r') as f:
            data = yaml.safe_load(f)
        data['project']['validation']['tests'] = tests_status
        with open(self.path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                return yaml.safe_load(f)
        return None
