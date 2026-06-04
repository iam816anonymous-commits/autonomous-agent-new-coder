import os
import ast

class ArchitectureExtractor:
    def __init__(self):
        pass

    def extract_structure(self, repo_path):
        """Builds a high-level map of the repository architecture and detects patterns."""
        structure = {
            "modules": [],
            "entry_points": [],
            "test_dirs": [],
            "patterns": [],
            "complexity_score": 0
        }

        file_count = 0
        for root, dirs, files in os.walk(repo_path):
            # Prune hidden dirs
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            rel_root = os.path.relpath(root, repo_path)
            file_count += len(files)

            # 1. Detect modules
            if "__init__.py" in files:
                structure["modules"].append(rel_root)

            # 2. Detect entry points and tests
            for f in files:
                full_path = os.path.join(root, f)
                if f in ["main.py", "app.py", "server.py", "index.ts"]:
                    structure["entry_points"].append(os.path.join(rel_root, f))
                if f.startswith("test_") or f.endswith("_test.py"):
                    if rel_root not in structure["test_dirs"]:
                        structure["test_dirs"].append(rel_root)

                # 3. Pattern Detection (Heuristic-based)
                content = ""
                if f.endswith(('.py', '.ts', '.js')):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as file:
                            content = file.read()
                    except: continue

                if "Agent" in content or "orchestrator" in content.lower():
                    self._add_pattern(structure, "Agent-based Reasoning")
                if "VectorStore" in content or "FAISS" in content or "Chroma" in content:
                    self._add_pattern(structure, "Semantic Memory (RAG)")
                if "JWT" in content or "auth" in content.lower():
                    self._add_pattern(structure, "JWT Authentication")
                if "@app.get" in content or "router" in content:
                    self._add_pattern(structure, "REST API Router")
                if "Provider" in content and ("router" in content.lower() or "llm" in content.lower()):
                    self._add_pattern(structure, "Provider Routing")
                if "docker-compose" in content or "Dockerfile" in files:
                    self._add_pattern(structure, "Containerized Deployment")
                if "pytest" in content or "unittest" in content:
                    self._add_pattern(structure, "Pytest-based Testing")
                if "Factory" in content:
                    self._add_pattern(structure, "Factory Pattern")
                if "Singleton" in content:
                    self._add_pattern(structure, "Singleton Pattern")

        # 4. Calculate Complexity Score (Normalized 0-100)
        structure["complexity_score"] = min(100, (len(structure["modules"]) * 5) + (file_count // 10))

        return structure

    def _add_pattern(self, structure, pattern):
        if pattern not in structure["patterns"]:
            structure["patterns"].append(pattern)

    def identify_arch_type(self, structure):
        if any("controllers" in m for m in structure["modules"]):
            return "MVC"
        if any("domain" in m for m in structure["modules"]):
            return "Domain Driven Design"
        if len(structure["modules"]) > 10:
            return "Microservices-ready Modular"
        return "Standard Monolith"
