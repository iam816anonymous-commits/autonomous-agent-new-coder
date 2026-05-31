import os
from project_creator.memory.vector_store import VectorStore

class SemanticSearch:
    def __init__(self, db_path):
        index_path = os.path.join(os.path.dirname(db_path), "brain_vectors.idx")
        self.vector_store = VectorStore(index_path)

    def index_knowledge(self, path, knowledge):
        """Indexes architectural findings semantically."""
        text = f"Repo: {path}\nArchitecture: {knowledge['architecture']['type']}\nDependencies: {', '.join(knowledge['dependencies'])}"
        self.vector_store.add(text, {
            "path": path,
            "type": "repo_knowledge",
            "arch": knowledge['architecture']['type']
        })

    def find_similar_projects(self, goal):
        return self.vector_store.search(goal, top_k=3)
