from project_creator.learning.memory_db import CodingMemory
from project_creator.memory.vector_store import VectorStore
import os

class ArchitectureMemory:
    def __init__(self, db_path):
        self.memory = CodingMemory(db_path)
        index_path = os.path.join(os.path.dirname(db_path), "arch_vectors.idx")
        self.vector_store = VectorStore(index_path)

    def store_architecture(self, project_type, architecture, deps, success_score=1.0):
        data = f"Project Type: {project_type}\nArch: {architecture}\nDeps: {', '.join(deps)}"
        self.vector_store.add(data, {
            "type": "architecture_template",
            "project_type": project_type,
            "architecture": architecture,
            "success_score": success_score
        })

    def retrieve_recommendation(self, goal):
        return self.vector_store.search(goal, top_k=2)
