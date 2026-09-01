import json
import time
from typing import Dict, Any, List, Optional
from repository.semantic.models import Evidence

class SemanticEvidenceTracker:
    """
    Records machine-readable structured evidence for definitions, calls, imports, and architecture findings.
    """
    def __init__(self, analysis_id: str):
        self.analysis_id = analysis_id
        self.evidence_records: List[Dict[str, Any]] = []

    def record_evidence(
        self,
        target: str,
        file: str,
        line: int,
        mechanism: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Evidence:
        ev = Evidence(
            file=file,
            line=line,
            extraction_mechanism=mechanism,
            confidence_reason=reason,
            metadata=metadata or {}
        )
        record = {
            "analysis_id": self.analysis_id,
            "target": target,
            "file": file,
            "line": line,
            "mechanism": mechanism,
            "reason": reason,
            "metadata": metadata or {},
            "timestamp": time.time()
        }
        self.evidence_records.append(record)
        return ev
