import re
import os

class DependencyAnalyzer:
    """
    Analyzes inter-file dependencies and determines the optimal generation order.
    """
    def __init__(self):
        self.dependencies = {} # path -> list of dependencies

    def analyze_project(self, blueprint_files):
        """
        Builds a dependency graph from file descriptions and paths.
        """
        for f in blueprint_files:
            path = f['path']
            desc = f.get('description', '')

            # Simple heuristic: look for file names mentioned in descriptions
            deps = []
            for other in blueprint_files:
                other_path = other['path']
                if other_path == path: continue

                # Check if other file name appears in description or if it's a 'core' file
                other_name = os.path.basename(other_path).split('.')[0]
                if other_name.lower() in desc.lower() or "core" in other_path:
                    deps.append(other_path)

            self.dependencies[path] = deps

        return self.dependencies

    def get_dependency_order(self):
        """
        Returns a topologically sorted list of files for generation.
        """
        visited = set()
        temp_visited = set()
        order = []

        def visit(node):
            if node in temp_visited:
                return # Circular dependency detected, skip or handle
            if node not in visited:
                temp_visited.add(node)
                for neighbor in self.dependencies.get(node, []):
                    visit(neighbor)
                temp_visited.remove(node)
                visited.add(node)
                order.append(node)

        for node in self.dependencies:
            visit(node)

        return order

    def _check_circular_dependencies(self):
        # Implementation of cycle detection logic
        pass

    def _check_missing_imports(self, content, path):
        # Scan code for imports and verify they exist in project
        pass
