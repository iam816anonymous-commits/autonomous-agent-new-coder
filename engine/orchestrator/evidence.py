import json
import time
from typing import Dict, Any, List, Optional
from engine.artifacts import ArtifactManager

class OrchestrationEvidenceCollector:
    """
    Collects structured, append-only, secret-redacted evidence throughout orchestration execution.
    """
    SECRET_KEYWORDS = ("api_key", "password", "token", "secret", "private_key", "auth")

    def __init__(self, task_id: str, artifact_manager: Optional[ArtifactManager] = None):
        self.task_id = task_id
        self.artifact_manager = artifact_manager or ArtifactManager()
        self.evidence_log: List[Dict[str, Any]] = []

    def sanitize(self, data: Any) -> Any:
        if isinstance(data, dict):
            sanitized = {}
            for k, v in data.items():
                if any(kw in str(k).lower() for kw in self.SECRET_KEYWORDS):
                    sanitized[k] = "[REDACTED_SECRET]"
                else:
                    sanitized[k] = self.sanitize(v)
            return sanitized
        elif isinstance(data, list):
            return [self.sanitize(item) for item in data]
        elif isinstance(data, str):
            for kw in ("sk-", "bearer "):
                if kw in data.lower():
                    return "[REDACTED_SECRET]"
            return data
        return data

    def record_event(self, event_type: str, details: Dict[str, Any]) -> None:
        clean_details = self.sanitize(details)
        evt = {
            "task_id": self.task_id,
            "event_type": event_type,
            "timestamp": time.time(),
            "details": clean_details
        }
        self.evidence_log.append(evt)
        filename = f"evidence_{int(time.time() * 1000)}.json"
        try:
            self.artifact_manager.write_artifact(f"task_{self.task_id}", filename, json.dumps(evt, indent=2))
        except Exception:
            pass
