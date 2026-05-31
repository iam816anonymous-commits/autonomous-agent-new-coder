import os

class ArchitectureExtractor:
    def extract(self, repo_path):
        """Identifies architectural patterns (e.g. MVC, Clean, Monolith)."""
        # Heuristic analysis based on folder structure
        structure = []
        for root, dirs, _ in os.walk(repo_path):
            rel_root = os.path.relpath(root, repo_path)
            if rel_root != '.':
                structure.append(rel_root)
            if len(structure) > 100: break # Safety cap

        arch_type = "unknown"
        if any("controllers" in s for s in structure) and any("models" in s for s in structure):
            arch_type = "MVC"
        elif any("domain" in s for s in structure) and any("infrastructure" in s for s in structure):
            arch_type = "Clean/Hexagonal"
        elif any("app" in s for s in structure) and any("core" in s for s in structure):
            arch_type = "Modular"

        return {
            "type": arch_type,
            "structure_sample": structure[:20]
        }
