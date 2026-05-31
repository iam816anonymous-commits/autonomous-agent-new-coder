import os
import ast
from project_creator.learning.memory_db import CodingMemory

class RepoIndexer:
    def __init__(self, db_path):
        self.memory = CodingMemory(db_path)

    def index_repo(self, repo_path):
        """Basic file-level indexing."""
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.tsx')):
                    path = os.path.join(root, file)
                    rel_path = os.path.relpath(path, repo_path)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Store snippet as approved pattern source
                            self.memory.add_snippet(rel_path, content, "INDEXED")
                    except Exception as e:
                        print(f"⚠️ Indexer: Failed to read {rel_path}: {e}")
