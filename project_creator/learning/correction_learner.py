import difflib
import os

from project_creator.memory.vector_store import VectorStore

from .event_bus import bus
from .memory_db import CodingMemory


class CorrectionLearner:
    def __init__(self, db_path: str):
        self.memory = CodingMemory(db_path)
        index_path = os.path.join(os.path.dirname(db_path), "jules_vectors.idx")
        self.vector_store = VectorStore(index_path)
        self._setup_subscriptions()

    def _setup_subscriptions(self):
        bus.subscribe("PATCH_REJECTED", self.learn_from_rejection)
        bus.subscribe("MANUAL_EDIT_DETECTED", self.learn_from_manual_correction)

    def learn_from_rejection(self, data):
        """Learns what the user didn't like."""
        path = data.get("path", "unknown")
        content = data.get("content", "")
        reason = data.get("reason", "User rejected patch")

        print(f"🚫 Learning from rejection: {path}")
        self.memory.add_anti_pattern(content[:1000], f"User Rejected: {reason}", "HIGH")

        # Store in vector store as a negative example
        self.vector_store.add(
            content,
            {"path": path, "type": "rejection", "reason": reason, "negative": True},
        )

    def learn_from_manual_correction(self, data):
        """Learns from the difference between Jules' code and the user's final version."""
        path = data.get("path")
        jules_code = data.get("jules_code")
        user_code = data.get("user_code")

        if not all([path, jules_code, user_code]):
            return

        print(f"🔧 Learning from manual correction: {path}")

        # Calculate diff to see what was changed
        diff = list(
            difflib.unified_diff(
                jules_code.splitlines(),
                user_code.splitlines(),
                fromfile="jules_version",
                tofile="user_version",
            )
        )

        if diff:
            diff_text = "\n".join(diff)
            # Store the correction as a high-preference pattern
            self.memory.learn_pattern("user_correction", diff_text)

            # Index the corrected version as the 'gold standard' for this context
            self.vector_store.add(
                user_code,
                {"path": path, "type": "correction", "original_was_jules": True},
            )
