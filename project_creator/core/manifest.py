import yaml
import os
import time

class ProjectManifest:
    def __init__(self, project_root):
        self.path = os.path.join(project_root, "project.yaml")

    def create(self, goal, stack, files):
        data = {
            "project": {
                "id": f"p_{int(time.time())}",
                "goal": goal,
                "stack": stack,
                "status": "active",
                "files": {f: {"status": "pending", "critique_history": []} for f in files},
                "approvals": [],
                "validation": {"tests": "pending"}
            }
        }
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

    def log_critique(self, path, critique):
        if not os.path.exists(self.path): return
        with open(self.path, 'r') as f:
            data = yaml.safe_load(f)

        if path in data['project']['files']:
            data['project']['files'][path]['critique_history'].append({
                "timestamp": time.time(),
                "verdict": critique.get('verdict'),
                "issues": critique.get('issues', [])
            })

        with open(self.path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

    def add_approval(self, path):
        if not os.path.exists(self.path): return
        with open(self.path, 'r') as f:
            data = yaml.safe_load(f)
        if path not in data['project']['approvals']:
            data['project']['approvals'].append(path)
        if path in data['project']['files']:
            data['project']['files'][path]['status'] = 'applied'

        with open(self.path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)

    def load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                return yaml.safe_load(f)
        return None

    def update_field(self, field, value):
        if not os.path.exists(self.path): return
        with open(self.path, 'r') as f:
            data = yaml.safe_load(f)

        # Support nested update for "project"
        data['project'][field] = value

        with open(self.path, 'w') as f:
            yaml.dump(data, f, sort_keys=False)
