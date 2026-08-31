import time
import uuid
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List

@dataclass
class WorkflowEvent:
    event_id: str
    workflow_id: str
    sequence_number: int
    event_type: str
    timestamp: float
    correlation_id: str
    payload: Dict[str, Any] = field(default_factory=dict)

class WorkflowEventLog:
    """
    Append-only, monotonically ordered, immutable workflow event logger.
    """
    SECRET_KEYS = ("api_key", "password", "token", "secret", "auth", "private_key")

    @classmethod
    def sanitize(cls, data: Any) -> Any:
        if isinstance(data, dict):
            sanitized = {}
            for k, v in data.items():
                if any(sk in str(k).lower() for sk in cls.SECRET_KEYS):
                    sanitized[k] = "[REDACTED_SECRET]"
                else:
                    sanitized[k] = cls.sanitize(v)
            return sanitized
        elif isinstance(data, list):
            return [cls.sanitize(item) for item in data]
        elif isinstance(data, str):
            for kw in ("sk-", "bearer "):
                if kw in data.lower():
                    return "[REDACTED_SECRET]"
            return data
        return data

    @classmethod
    def create_event(
        cls,
        workflow_id: str,
        sequence_number: int,
        event_type: str,
        correlation_id: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> WorkflowEvent:
        event_id = f"wfe-{uuid.uuid4().hex[:12]}"
        clean_payload = cls.sanitize(payload or {})
        return WorkflowEvent(
            event_id=event_id,
            workflow_id=workflow_id,
            sequence_number=sequence_number,
            event_type=event_type,
            timestamp=time.time(),
            correlation_id=correlation_id,
            payload=clean_payload
        )
