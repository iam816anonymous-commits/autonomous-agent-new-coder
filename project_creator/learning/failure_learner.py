from .event_bus import bus
from .memory_db import CodingMemory

class FailureLearner:
    def __init__(self, db_path: str):
        self.memory = CodingMemory(db_path)
        self._setup_subscriptions()

    def _setup_subscriptions(self):
        bus.subscribe("VALIDATION_FAILED", self.on_failure)
        bus.subscribe("CRITIQUE_FAILED", self.on_failure)

    def on_failure(self, data):
        f_type = data.get('type', 'GENERIC_FAILURE')
        path = data.get('path', 'unknown')
        error = data.get('error', 'No error message provided')
        context = data.get('content', '')

        print(f"📉 Learning from failure: {f_type} at {path}")
        self.memory.log_failure(f_type, path, error, context)

        # Add to anti-patterns if specific enough
        if "SyntaxError" in error:
            self.memory.add_anti_pattern(context[:500], "Syntax Error detected during dry-run", "MEDIUM")
        elif "Unused import" in error:
             self.memory.add_anti_pattern(error, "Linter violation: Unused import", "LOW")
