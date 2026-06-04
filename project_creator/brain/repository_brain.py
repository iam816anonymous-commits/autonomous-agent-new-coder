from .repo_indexer import RepoIndexer
from .architecture_extractor import ArchitectureExtractor
from .dependency_extractor import DependencyExtractor
from .repository_memory import RepositoryMemory
from .architecture_memory import ArchitectureMemory
import os
import json

class RepositoryBrain:
    def __init__(self, db_path):
        self.indexer = RepoIndexer(db_path)
        self.arch_extractor = ArchitectureExtractor()
        self.dep_extractor = DependencyExtractor()
        self.repo_memory = RepositoryMemory(db_path)
        self.arch_memory = ArchitectureMemory(db_path)

    def ingest_repository(self, repo_path):
        """
        Scan, extract knowledge card, and store patterns.
        """
        repo_name = os.path.basename(repo_path)
        print(f"🧠 Brain: Starting ingestion for {repo_name}")

        # 1. Index source code patterns
        file_map = self.indexer.scan_repo(repo_path)

        # 2. Extract Architecture & Patterns
        structure = self.arch_extractor.extract_structure(repo_path)
        arch_type = self.arch_extractor.identify_arch_type(structure)

        # 3. Extract Dependencies
        dependencies = self.dep_extractor.extract_dependencies(repo_path)

        # 4. Generate Knowledge Card
        card = {
            "repository": repo_name,
            "category": "External Learning",
            "architecture": arch_type,
            "patterns": structure["patterns"],
            "dependencies": dependencies["python"] + dependencies["javascript"],
            "complexity_score": structure["complexity_score"],
            "confidence": 0.85 # Heuristic confidence
        }

        # 5. Store in specialized memories
        self.repo_memory.store_card(card)
        self.arch_memory.store_architecture(
            project_type=card["category"],
            architecture=card["architecture"],
            dependencies=card["dependencies"],
            success_score=card["confidence"]
        )

        # Save card to project root for inspection if needed
        try:
            with open(os.path.join(repo_path, "repository_card.json"), 'w') as f:
                json.dump(card, f, indent=2)
        except: pass

        print(f"✅ Brain: Ingested {repo_name}. Complexity: {card['complexity_score']}, Patterns: {len(card['patterns'])}")
        return card
