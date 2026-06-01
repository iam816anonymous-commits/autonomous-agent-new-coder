from project_creator.learning.memory_db import CodingMemory
from project_creator.memory.vector_store import VectorStore
import os

class RepairMemory:
    def __init__(self, db_path):
        self.sql_memory = CodingMemory(db_path)
        # Brain-specific vector index
        brain_dir = os.path.dirname(db_path)
        self.vector_store = VectorStore(os.path.join(brain_dir, "brain_repair.idx"))

    def store_repair(self, error, traceback, root_cause, repair, success_rate=1.0):
        """Stores a validated repair pattern."""
        entry = {
            "error": error,
            "traceback": traceback,
            "root_cause": root_cause,
            "repair": repair,
            "success_rate": success_rate
        }
        # Store in vector for semantic retrieval
        text_context = f"Error: {error}\nTraceback: {traceback}\nRoot Cause: {root_cause}\nRepair: {repair}"
        self.vector_store.add(text_context, entry)

        # Also log to SQL failures for general activity tracking
        self.sql_memory.log_failure("REPAIR_MEMORY_UPGRADE", "brain", error, repair)

    def retrieve_repairs(self, error_msg, top_k=3):
        return self.vector_store.search(error_msg, top_k=top_k)
