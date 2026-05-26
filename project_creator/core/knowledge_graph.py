import ast
import os

class KnowledgeGraph:
    @staticmethod
    def analyze_file(file_path, content):
        """Extracts dependencies and basic metrics from a Python file."""
        if not file_path.endswith(".py"):
            return {"dependencies": [], "risk_score": 0.1}

        try:
            tree = ast.parse(content)
            deps = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        deps.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    deps.append(node.module)

            # Simple risk heuristic: more lines/complexity = higher risk
            lines = content.count('\n')
            risk = min(1.0, lines / 500.0)

            return {
                "dependencies": list(set(filter(None, deps))),
                "risk_score": risk
            }
        except:
            return {"dependencies": [], "risk_score": 0.5}

    @staticmethod
    def get_owner_agent(file_path):
        # Heuristic for which agent likely 'owns' or handles this file
        if "test" in file_path: return "TestAgent"
        if "provider" in file_path: return "ProviderAgent"
        if "core" in file_path: return "SystemAgent"
        return "FeatureAgent"
