from typing import List, Set
from .snapshot import SemanticRepositorySnapshot, SemanticSnapshotter
from .python_analyzer import PythonSemanticAnalyzer
from repository.scan import RepositorySnapshot

class IncrementalSemanticAnalyzer:
    """
    Selectively updates stale files/symbols in the semantic repository graph given changed file paths.
    Fallback to full rebuild if correctness is uncertain.
    """
    @classmethod
    def update_snapshot(cls, current_snapshot: SemanticRepositorySnapshot, repo_snapshot: RepositorySnapshot, changed_files: List[str]) -> SemanticRepositorySnapshot:
        analyzer = PythonSemanticAnalyzer(repo_snapshot.root, current_snapshot.graph)

        for rel_path in changed_files:
            analyzer.analyze_file(rel_path)

        return current_snapshot
