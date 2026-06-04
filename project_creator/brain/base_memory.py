import os
from project_creator.memory.vector_store import VectorStore
from project_creator.learning.memory_db import CodingMemory

class BaseBrainMemory:
    """
    Base class for brain memory modules providing consistent vector and SQL access.
    """
    def __init__(self, db_path, index_name=None):
        self.sql_memory = CodingMemory(db_path)
        if index_name:
            brain_dir = os.path.dirname(db_path)
            self.vector_store = VectorStore(os.path.join(brain_dir, f"brain_{index_name}.idx"))
        else:
            self.vector_store = None

    def search(self, query, top_k=3):
        if not self.vector_store:
            return []
        return self.vector_store.search(query, top_k=top_k)
