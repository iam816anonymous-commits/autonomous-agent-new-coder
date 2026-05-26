import os
import json

class Storage:
    def __init__(self, project_root):
        self.project_root = os.path.abspath(project_root)
        self.state_file = os.path.join(self.project_root, ".agent_state.json")

    def _safe_join(self, *paths):
        joined_path = os.path.join(self.project_root, *paths)
        final_path = os.path.abspath(joined_path)
        if not final_path.startswith(self.project_root):
            raise ValueError(f"Security Warning: Path traversal attempt: {final_path}")
        return final_path

    def ensure_directory(self, path):
        full_path = self._safe_join(os.path.dirname(path))
        if full_path and not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)

    def write_file(self, path, content):
        # Apply Governance Boundary Check
        try:
            from project_creator.core.governance import GovernanceLayer
            GovernanceLayer.enforce_boundary(path)
        except ImportError:
            pass # Handle bootstrap cases

        full_path = self._safe_join(path)
        self.ensure_directory(path)

        # In this OS version, we overwrite more freely in candidate branches
        # but the main OS should respect it.
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    def save_state(self, state):
        os.makedirs(self.project_root, exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)

    def load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def read_existing_files(self):
        files_context = {}
        if not os.path.exists(self.project_root): return files_context
        ignored_dirs = {'.git', '__pycache__', 'node_modules', '.agent_memory.db'}
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            for file in files:
                if file == ".agent_state.json": continue
                rel_path = os.path.relpath(os.path.join(root, file), self.project_root)
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        files_context[rel_path] = f.read()
                except: pass
        return files_context
