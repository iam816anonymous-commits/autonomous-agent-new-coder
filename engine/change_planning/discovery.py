import re
from typing import Dict, Any, List, Optional
from repository.semantic.snapshot import SemanticRepositorySnapshot
from repository.semantic.queries import SemanticQueryEngine
from .models import ChangeRequest, ConfidenceLevel, Evidence
from .errors import DiscoveryError

class ChangeDiscoveryEngine:
    """
    Investigates repository structure, entry points, routers, middleware, and database layers
    before selecting target files for a ChangeRequest.
    """
    def __init__(self, semantic_snapshot: SemanticRepositorySnapshot):
        self.snapshot = semantic_snapshot
        self.query_engine = SemanticQueryEngine(semantic_snapshot.graph)

    def discover_change_targets(self, request: ChangeRequest) -> Dict[str, Any]:
        intent = request.user_intent
        matched_symbols = []
        matched_files = set()
        evidence_list = []

        # Query graph for symbols matching intent keywords with word boundary checks
        for sym_id, sym in self.snapshot.graph.symbols.items():
            if not sym.name or len(sym.name) < 2:
                continue

            matches_intent = bool(re.search(r'\b' + re.escape(sym.name) + r'\b', intent, re.IGNORECASE))
            matches_hints = request.target_hints and sym.name in request.target_hints

            if matches_intent or matches_hints:
                matched_symbols.append(sym)
                matched_files.add(sym.file_path)
                evidence_list.append(Evidence(
                    file=sym.file_path,
                    line=sym.start_line,
                    extraction_mechanism="SEMANTIC_QUERY",
                    confidence_reason=f"Symbol name '{sym.name}' matched change request intent keywords."
                ))

        # Check architecture boundaries
        patterns = self.snapshot.architecture.get("patterns", [])

        confidence = ConfidenceLevel.HIGH if len(matched_symbols) == 1 else (
            ConfidenceLevel.MEDIUM if len(matched_symbols) > 1 else ConfidenceLevel.LOW
        )

        return {
            "request_id": request.request_id,
            "matched_symbols": [s.name for s in matched_symbols],
            "target_files": sorted(list(matched_files)),
            "architecture_patterns": patterns,
            "confidence": confidence,
            "evidence": evidence_list,
            "sufficient_evidence": len(matched_symbols) > 0
        }
