import ast
import os
import re
import sys
from typing import List, Dict, Set, Tuple, Optional
from .models import DependencyEdge, DependencyType, DependencyGraphModel

STDLIB_MODULES = set(sys.builtin_module_names) | {
    "os", "sys", "re", "json", "ast", "time", "datetime", "math", "random",
    "collections", "itertools", "functools", "typing", "pathlib", "shutil",
    "subprocess", "tempfile", "logging", "unittest", "sqlite3", "hashlib",
    "dataclasses", "enum", "shlex", "difflib", "asyncio", "threading"
}

class DependencyGraphBuilder:
    """
    Builds static file, module, and symbol dependency graphs and detects cycles and unresolved imports.
    Operates 100% deterministically without LLMs.
    """
    def __init__(self, root: str):
        self.root = os.path.realpath(os.path.abspath(root))
        self.edges: List[DependencyEdge] = []
        self.file_dependencies: Dict[str, Set[str]] = {} # src -> set of targets
        self.file_dependents: Dict[str, Set[str]] = {} # target -> set of srcs
        self.unresolved_imports: List[Dict[str, str]] = []
        self.all_files: Set[str] = set()

    def build_graph(self, file_paths: List[str]) -> DependencyGraphModel:
        self.edges.clear()
        self.file_dependencies.clear()
        self.file_dependents.clear()
        self.unresolved_imports.clear()
        self.all_files = set(file_paths)

        for rel_path in file_paths:
            self.file_dependencies[rel_path] = set()
            if rel_path not in self.file_dependents:
                self.file_dependents[rel_path] = set()

        for rel_path in file_paths:
            full_path = os.path.join(self.root, rel_path)
            if not os.path.exists(full_path):
                continue

            if rel_path.endswith('.py'):
                self._analyze_python_dependencies(rel_path, full_path)
            elif rel_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                self._analyze_jsts_dependencies(rel_path, full_path)

        cycles = self.detect_cycles()

        return DependencyGraphModel(
            nodes=sorted(list(self.all_files)),
            edges=self.edges,
            cycles=cycles,
            unresolved_imports=self.unresolved_imports
        )

    def _add_edge(self, source: str, target: str, dep_type: DependencyType, symbol_name: Optional[str] = None):
        edge = DependencyEdge(source=source, target=target, dependency_type=dep_type, symbol_name=symbol_name)
        self.edges.append(edge)

        if dep_type == DependencyType.LOCAL_FILE and target in self.all_files:
            self.file_dependencies[source].add(target)
            if target not in self.file_dependents:
                self.file_dependents[target] = set()
            self.file_dependents[target].add(source)

    def _analyze_python_dependencies(self, rel_path: str, full_path: str):
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            tree = ast.parse(content, filename=rel_path)
        except Exception:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod_name = alias.name
                    self._resolve_python_import(rel_path, mod_name)
            elif isinstance(node, ast.ImportFrom):
                mod_name = node.module or ""
                level = node.level
                self._resolve_python_import_from(rel_path, mod_name, level, [a.name for a in node.names])

    def _resolve_python_import(self, source_file: str, mod_name: str):
        base_mod = mod_name.split('.')[0]

        if base_mod in STDLIB_MODULES:
            self._add_edge(source_file, mod_name, DependencyType.STDLIB)
            return

        # Attempt local resolution
        mod_rel_path = mod_name.replace('.', '/') + '.py'
        mod_init_path = mod_name.replace('.', '/') + '/__init__.py'

        if mod_rel_path in self.all_files:
            self._add_edge(source_file, mod_rel_path, DependencyType.LOCAL_FILE)
        elif mod_init_path in self.all_files:
            self._add_edge(source_file, mod_init_path, DependencyType.LOCAL_FILE)
        else:
            # Check if it's top-level local package or third-party
            potential_file = os.path.join(self.root, mod_rel_path)
            if os.path.exists(potential_file):
                self._add_edge(source_file, mod_rel_path, DependencyType.LOCAL_FILE)
            else:
                self._add_edge(source_file, mod_name, DependencyType.THIRD_PARTY)

    def _resolve_python_import_from(self, source_file: str, mod_name: str, level: int, symbol_names: List[str]):
        if level > 0:
            # Relative import
            dir_parts = os.path.dirname(source_file).split('/') if '/' in source_file else (['.'] if source_file else [])
            for _ in range(level - 1):
                if dir_parts and dir_parts != ['.']:
                    dir_parts.pop()

            base_dir = "/".join(dir_parts) if dir_parts and dir_parts != ['.'] else ""
            target_base = f"{base_dir}/{mod_name.replace('.', '/')}" if base_dir and mod_name else (base_dir or mod_name.replace('.', '/'))
            target_base = target_base.strip('/')

            mod_rel = target_base + '.py'
            mod_init = target_base + '/__init__.py'

            if mod_rel in self.all_files:
                for sym in symbol_names:
                    self._add_edge(source_file, mod_rel, DependencyType.LOCAL_FILE, symbol_name=sym)
            elif mod_init in self.all_files:
                for sym in symbol_names:
                    self._add_edge(source_file, mod_init, DependencyType.LOCAL_FILE, symbol_name=sym)
            else:
                self.unresolved_imports.append({
                    "source": source_file,
                    "import": f"from {'.' * level}{mod_name} import {', '.join(symbol_names)}"
                })
        else:
            self._resolve_python_import(source_file, mod_name)

    def _analyze_jsts_dependencies(self, rel_path: str, full_path: str):
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return

        import_pattern = re.compile(r'(?:import|require)\s*(?:\(\s*[\'"]([^\'"]+)[\'"]\s*\)|.*?from\s*[\'"]([^\'"]+)[\'"])')

        for match in import_pattern.finditer(content):
            import_path = match.group(1) or match.group(2)
            if not import_path:
                continue

            if import_path.startswith('.'):
                # Local relative import
                resolved = self._resolve_jsts_relative_import(rel_path, import_path)
                if resolved:
                    self._add_edge(rel_path, resolved, DependencyType.LOCAL_FILE)
                else:
                    self.unresolved_imports.append({
                        "source": rel_path,
                        "import": import_path
                    })
            else:
                self._add_edge(rel_path, import_path, DependencyType.THIRD_PARTY)

    def _resolve_jsts_relative_import(self, source_file: str, relative_import: str) -> Optional[str]:
        source_dir = os.path.dirname(source_file)
        joined = os.path.normpath(os.path.join(source_dir, relative_import)).replace("\\", "/")

        extensions = ['', '.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.tsx', '/index.js', '/index.jsx']

        for ext in extensions:
            candidate = joined + ext
            if candidate in self.all_files:
                return candidate
        return None

    def get_dependencies(self, node: str) -> List[str]:
        return sorted(list(self.file_dependencies.get(node, set())))

    def get_dependents(self, node: str) -> List[str]:
        return sorted(list(self.file_dependents.get(node, set())))

    def get_related_tests(self, node: str) -> List[str]:
        dependents = self.get_dependents(node)
        related = set()

        for dep in dependents + [node]:
            if "test" in dep.lower() or dep.startswith("tests/"):
                related.add(dep)

        node_base = os.path.basename(node).split('.')[0]
        for f in self.all_files:
            if "test" in f.lower():
                if node_base in os.path.basename(f):
                    related.add(f)

        return sorted(list(related))

    def detect_cycles(self) -> List[List[str]]:
        """Detects circular dependency loops using DFS."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []
        cycles: List[List[str]] = []

        def dfs(node: str):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in sorted(list(self.file_dependencies.get(node, set()))):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Cycle found
                    cycle_start = path.index(neighbor)
                    cycle_path = path[cycle_start:] + [neighbor]
                    cycles.append(cycle_path)

            path.pop()
            rec_stack.remove(node)

        for n in sorted(list(self.all_files)):
            if n not in visited:
                dfs(n)

        return cycles

    def has_cycle(self) -> bool:
        return len(self.detect_cycles()) > 0

    def topological_order(self) -> List[str]:
        """Returns a topologically sorted order of files for deterministic generation (dependencies first)."""
        # Count in_degree as number of unhandled dependencies a file has
        in_degree = {f: len(self.file_dependencies.get(f, set())) for f in self.all_files}

        # Files with 0 dependencies can be generated first
        queue = sorted([f for f in self.all_files if in_degree[f] == 0])
        order = []

        while queue:
            node = queue.pop(0)
            order.append(node)

            # For every file that depends on `node` (dependent), reduce its pending dependency count
            for dependent in sorted(list(self.file_dependents.get(node, set()))):
                if dependent in in_degree and in_degree[dependent] > 0:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
                        queue.sort()

        # Add remaining files if cycles exist
        for f in sorted(list(self.all_files)):
            if f not in order:
                order.append(f)

        return order
