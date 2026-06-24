import re
import time

from .constitution import LearningConstitution
from .event_bus import bus


class ActivityCollector:
    def __init__(self):
        self.events = []
        self.exclude_patterns = [
            r"\.env$",
            r"\.git/",
            r"node_modules/",
            r"venv/",
            r"secrets",
            r"tokens",
            r"cookies\.json",
        ]

    def _is_safe(self, path: str):
        for pattern in self.exclude_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                return False
        return True

    def collect(self, event_type: str, data: dict):
        if "path" in data and not self._is_safe(data["path"]):
            print(f"🛡️  Learning Collector: Blocked unsafe path {data['path']}")
            return

        # Apply Constitution Scrubbing
        if "content" in data:
            data["content"] = LearningConstitution.scrub(data["content"])

        event = {"type": event_type, "timestamp": time.time(), "data": data}
        self.events.append(event)
        bus.publish(event_type, data)
        print(f"📊 Activity Logged: {event_type}")


collector = ActivityCollector()
