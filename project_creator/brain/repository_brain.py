from .repo_indexer import RepoIndexer
from .architecture_extractor import ArchitectureExtractor
from .dependency_extractor import DependencyExtractor
import os

class RepositoryBrain:
    def __init__(self, db_path):
        self.indexer = RepoIndexer(db_path)
        self.arch_extractor = ArchitectureExtractor()
        self.dep_extractor = DependencyExtractor()

    def ingest_repository(self, repo_path):
        """
        Scan and store everything about a repository.
        """
        print(f"🧠 Brain: Starting ingestion for {repo_path}")

        # 1. Index source code
        file_map = self.indexer.scan_repo(repo_path)

        # 2. Extract Architecture
        structure = self.arch_extractor.extract_structure(repo_path)
        arch_type = self.arch_extractor.identify_arch_type(structure)

        # 3. Extract Dependencies
        dependencies = self.dep_extractor.extract_dependencies(repo_path)

        knowledge = {
            "path": repo_path,
            "architecture": arch_type,
            "structure": structure,
            "dependencies": dependencies,
            "file_count": len(file_map)
        }

        print(f"✅ Brain: Ingested {knowledge['file_count']} files. Architecture: {arch_type}")
        return knowledge
