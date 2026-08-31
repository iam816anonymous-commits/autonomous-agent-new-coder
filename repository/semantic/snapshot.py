import os
import hashlib
from dataclasses import dataclass, field
from typing import Dict, Any, List
from .graph import SemanticRepositoryGraph
from .architecture import ArchitectureDetector
from repository.scan import RepositorySnapshot

@dataclass
class SemanticRepositorySnapshot:
    repository_fingerprint: str
    graph: SemanticRepositoryGraph
    architecture: Dict[str, Any] = field(default_factory=dict)
    analysis_version: str = "v1.0"

class SemanticSnapshotter:
    @classmethod
    def capture(cls, repo_snapshot: RepositorySnapshot) -> SemanticRepositorySnapshot:
        from .python_analyzer import PythonSemanticAnalyzer

        graph = SemanticRepositoryGraph()
        analyzer = PythonSemanticAnalyzer(repo_snapshot.root, graph)

        for src in repo_snapshot.info.source_files + repo_snapshot.info.test_files:
            analyzer.analyze_file(src)

        arch = ArchitectureDetector.detect_architecture(repo_snapshot.info)
        fingerprint = getattr(repo_snapshot, "summary_hash", hashlib.sha256(repo_snapshot.root.encode("utf-8")).hexdigest()[:12])

        return SemanticRepositorySnapshot(
            repository_fingerprint=fingerprint,
            graph=graph,
            architecture=arch
        )
