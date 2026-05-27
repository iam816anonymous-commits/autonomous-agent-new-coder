import os
import re
from .event_bus import bus
from .collector import collector

class RepoLearner:
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.exclude_dirs = {'.git', 'node_modules', 'venv', '__pycache__', 'dist', 'build'}
        self.include_exts = {'.py', '.js', '.ts', '.tsx', '.go', '.rs', '.java', '.cpp'}

    def scan_workspace(self):
        print(f"🔍 Reality Learning: Scanning workspace {self.workspace_root}")
        for root, dirs, files in os.walk(self.workspace_root):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]

            for file in files:
                if any(file.endswith(ext) for ext in self.include_exts):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.workspace_root)

                    if not collector._is_safe(rel_path):
                        continue

                    self._learn_file(file_path, rel_path)

    def _learn_file(self, full_path: str, rel_path: str):
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if content:
                    bus.publish("FILE_OPEN", {
                        "path": rel_path,
                        "content": content
                    })
        except Exception as e:
            print(f"⚠️  RepoLearner: Failed to read {rel_path}: {e}")
