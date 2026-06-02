import ast
import os
from typing import Dict, List, Set

class CallGraphLearner:
    """
    Uses AST to map function calls and class inheritances across a repository.
    """
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.call_graph = {} # caller -> set of callees
        self.class_graph = {} # class -> set of bases

    def build_graph(self):
        print(f"📊 [AST] Building call graph for {self.project_root}")
        for root, _, files in os.walk(self.project_root):
            for file in files:
                if file.endswith('.py'):
                    self._analyze_file(os.path.join(root, file))

    def _analyze_file(self, file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())

            rel_path = os.path.relpath(file_path, self.project_root)

            for node in ast.walk(tree):
                # Class Analysis
                if isinstance(node, ast.ClassDef):
                    bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
                    self.class_graph[f"{rel_path}:{node.name}"] = bases

                # Call Analysis
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        callee = node.func.id
                        # This is a simplification; real call graphs need scope tracking
                        caller = "global"
                        if callee not in self.call_graph: self.call_graph[callee] = set()
                        # We'd ideally track which function we are currently inside
        except: pass

    def get_impacted_files(self, modified_file: str) -> List[str]:
        """Heuristic to find files that might break if modified_file changes."""
        # This implementation would search the call/import graph
        return []
