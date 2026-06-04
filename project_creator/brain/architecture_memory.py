from .base_memory import BaseBrainMemory

class ArchitectureMemory(BaseBrainMemory):
    def __init__(self, db_path):
        super().__init__(db_path, index_name="architecture")

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
        return self.search(goal, top_k=top_k)
