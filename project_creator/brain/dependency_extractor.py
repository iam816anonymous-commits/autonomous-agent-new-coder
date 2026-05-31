import os
import re

class DependencyExtractor:
    def extract(self, repo_path):
        """Extracts dependencies from requirements.txt, package.json, etc."""
        deps = []

        # Python
        req_path = os.path.join(repo_path, "requirements.txt")
        if os.path.exists(req_path):
            with open(req_path, 'r') as f:
                deps.extend([line.strip() for line in f if line.strip() and not line.startswith('#')])

        # JS/TS
        pkg_path = os.path.join(repo_path, "package.json")
        if os.path.exists(pkg_path):
            try:
                import json
                with open(pkg_path, 'r') as f:
                    data = json.load(f)
                    deps.extend(data.get('dependencies', {}).keys())
                    deps.extend(data.get('devDependencies', {}).keys())
            except: pass

        return list(set(deps))
