from project_creator.memory.vector_store import VectorStore
import os

class ArchitectureMemory:
    def __init__(self, db_path):
        brain_dir = os.path.dirname(db_path)
        self.vector_store = VectorStore(os.path.join(brain_dir, "brain_architecture.idx"))

    def store_architecture(self, project_type, architecture, dependencies, success_score=1.0):
        entry = {
            "project_type": project_type,
            "architecture": architecture,
            "dependencies": dependencies,
            "success_score": success_score
        }
        text_context = f"Project Type: {project_type}\nArchitecture: {architecture}\nDeps: {', '.join(dependencies)}"
        self.vector_store.add(text_context, entry)

    def retrieve_similar(self, goal, top_k=2):
        return self.vector_store.search(goal, top_k=top_k)
