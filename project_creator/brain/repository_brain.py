import os
from .repo_indexer import RepoIndexer
from .architecture_extractor import ArchitectureExtractor
from .dependency_extractor import DependencyExtractor
from .semantic_search import SemanticSearch

class RepositoryBrain:
    """
    Orchestrates the understanding of external repositories.
    """
    def __init__(self, db_path):
        self.indexer = RepoIndexer(db_path)
        self.arch_extractor = ArchitectureExtractor()
        self.dep_extractor = DependencyExtractor()
        self.search = SemanticSearch(db_path)

    def learn_repository(self, repo_path):
        print(f"🧠 Brain: Ingesting repository {repo_path}")

        # 1. Index Files
        self.indexer.index_repo(repo_path)

        # 2. Extract Architecture
        arch = self.arch_extractor.extract(repo_path)

        # 3. Extract Dependencies
        deps = self.dep_extractor.extract(repo_path)

        # 4. Save to searchable memory
        self.search.index_knowledge(repo_path, {
            "architecture": arch,
            "dependencies": deps
        })

        return {
            "path": repo_path,
            "architecture": arch,
            "dependencies": deps
        }
