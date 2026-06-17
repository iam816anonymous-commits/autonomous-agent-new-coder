import ast
import os
from typing import List


class CallGraphLearner:
    """
    Uses AST to map function calls and class inheritances across a repository.
    """

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.call_graph = {}  # caller -> set of callees
        self.class_graph = {}  # class -> set of bases

    def build_graph(self):
        print(f"📊 [AST] Building call graph for {self.project_root}")
        for root, _, files in os.walk(self.project_root):
            for file in files:
                if file.endswith(".py"):
                    self._analyze_file(os.path.join(root, file))

    def _analyze_file(self, file_path: str):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            rel_path = os.path.relpath(file_path, self.project_root)
            current_container = "global"

            for node in ast.walk(tree):
                # Context tracking
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    current_container = f"{rel_path}:{node.name}"
                elif isinstance(node, ast.ClassDef):
                    current_container = f"{rel_path}:{node.name}"
                    bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
                    self.class_graph[current_container] = bases

                # Call Analysis
                if isinstance(node, ast.Call):
                    callee = None
                    if isinstance(node.func, ast.Name):
                        callee = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        callee = node.func.attr

                    if callee:
                        if callee not in self.call_graph:
                            self.call_graph[callee] = set()
                        self.call_graph[callee].add(current_container)
        except:
            pass

    def get_impacted_files(self, modified_file: str) -> List[str]:
        """Identifies files that call functions defined in the modified_file."""
        impacted = set()

        # 1. Re-analyze modified file to find what it defines
        defined_funcs = set()
        try:
            full_path = os.path.join(self.project_root, modified_file)
            with open(full_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                ):
                    defined_funcs.add(node.name)
        except:
            return []

        # 2. Find who calls those functions
        for func in defined_funcs:
            callers = self.call_graph.get(func, set())
            for caller in callers:
                file_part = caller.split(":")[0]
                if file_part != modified_file:
                    impacted.add(file_part)

        return list(impacted)
