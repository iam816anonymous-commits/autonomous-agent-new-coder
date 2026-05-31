from project_creator.learning.memory_db import CodingMemory
from project_creator.memory.vector_store import VectorStore
import os

class RepairMemory:
    def __init__(self, db_path):
        self.memory = CodingMemory(db_path)
        index_path = os.path.join(os.path.dirname(db_path), "jules_vectors.idx")
        self.vector_store = VectorStore(index_path)

    def store_repair(self, error, traceback, root_cause, repair, success=True):
        data = f"Error: {error}\nCause: {root_cause}\nRepair: {repair}"
        self.vector_store.add(data, {
            "type": "repair_pattern",
            "error": error,
            "success": success
        })
        # Log to SQL as failure/correction
        self.memory.log_failure("REPAIR_STORE", "brain", error, traceback)

    def retrieve_similar_repairs(self, error_msg):
        return self.vector_store.search(error_msg, top_k=3)
