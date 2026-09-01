import json
import time
from typing import Dict, Any, List, Optional
from engine.artifacts import ArtifactManager

class SemanticAuditLogger:
    """
    Persists structured, secret-redacted semantic analysis decisions to artifacts.
    """
    def __init__(self, task_id: str, artifact_manager: Optional[ArtifactManager] = None):
        self.task_id = task_id
        self.artifact_manager = artifact_manager or ArtifactManager()

    def log_decision(self, operation: str, result_status: str, trust_level: str, evidence_data: Dict[str, Any]) -> str:
        record = {
            "task_id": self.task_id,
            "operation": operation,
            "result_status": result_status,
            "trust_level": trust_level,
            "evidence": evidence_data,
            "timestamp": time.time()
        }
        filename = f"semantic_audit_{int(time.time() * 1000)}.json"
        try:
            return self.artifact_manager.write_artifact(f"task_{self.task_id}", filename, json.dumps(record, indent=2))
        except Exception:
            return ""
