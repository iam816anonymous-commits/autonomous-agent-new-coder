from .base_memory import BaseBrainMemory

class RepairMemory(BaseBrainMemory):
    def __init__(self, db_path):
        super().__init__(db_path, index_name="repair")

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
        return self.search(error_msg, top_k=top_k)
