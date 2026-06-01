import os
import ast

class ArchitectureExtractor:
    def __init__(self):
        pass

    def extract_structure(self, repo_path):
        """Builds a high-level map of the repository architecture."""
        structure = {
            "modules": [],
            "entry_points": [],
            "test_dirs": [],
            "patterns": []
        }

        for root, dirs, files in os.walk(repo_path):
            rel_root = os.path.relpath(root, repo_path)
            if rel_root == '.': continue

            # Detect modules
            if "__init__.py" in files:
                structure["modules"].append(rel_root)

            # Detect entry points
            for f in files:
                if f in ["main.py", "app.py", "server.py", "index.ts"]:
                    structure["entry_points"].append(os.path.join(rel_root, f))
                if f.startswith("test_") or f.endswith("_test.py"):
                    if rel_root not in structure["test_dirs"]:
                        structure["test_dirs"].append(rel_root)

        return structure

    def identify_arch_type(self, structure):
        if any("controllers" in m for m in structure["modules"]):
            return "MVC"
        if any("domain" in m for m in structure["modules"]):
            return "Domain Driven Design"
        if len(structure["modules"]) > 10:
            return "Microservices-ready Modular"
        return "Standard Monolith"
