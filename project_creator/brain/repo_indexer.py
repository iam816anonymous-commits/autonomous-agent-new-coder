import os
import ast
from project_creator.learning.memory_db import CodingMemory

class RepoIndexer:
    def __init__(self, db_path):
        self.memory = CodingMemory(db_path)

    def scan_repo(self, repo_path):
        print(f"🔍 Indexing Repository: {repo_path}")
        file_map = {}
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.tsx')):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, repo_path)
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            file_map[rel_path] = content
                            # Feed to underlying pattern memory
                            self.memory.add_snippet(rel_path, content, "INDEXED")

                            # Also feed to PatternLearner for deep structural learning
                            from project_creator.learning import pattern_learner
                            pattern_learner.learn_from_file({"path": rel_path, "content": content})
                    except Exception as e:
                        print(f"⚠️  Indexer skip {rel_path}: {e}")
        return file_map
