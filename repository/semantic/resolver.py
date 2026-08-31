from typing import Dict, Any, List, Optional
from .graph import SemanticRepositoryGraph
from .models import SemanticSymbol, ConfidenceLevel, SymbolKind
from .errors import SymbolResolutionError, AmbiguousSymbolError

class SemanticResolver:
    """
    Resolves symbol definitions, qualified names, and references.
    Explicitly reports RESOLVED, AMBIGUOUS, UNRESOLVED, or UNSUPPORTED with confidence bounds.
    """
    def __init__(self, graph: SemanticRepositoryGraph):
        self.graph = graph

    def resolve_definition(self, query: str, context_file: Optional[str] = None) -> Dict[str, Any]:
        defs = self.graph.find_definitions(query)

        if not defs:
            return {
                "status": "UNRESOLVED",
                "symbol_name": query,
                "confidence": ConfidenceLevel.UNKNOWN,
                "matches": []
            }

        if context_file:
            # Filter matches in same file first
            same_file = [s for s in defs if s.file_path == context_file]
            if len(same_file) == 1:
                return {
                    "status": "RESOLVED",
                    "symbol": same_file[0],
                    "confidence": ConfidenceLevel.HIGH,
                    "matches": same_file
                }

        if len(defs) == 1:
            return {
                "status": "RESOLVED",
                "symbol": defs[0],
                "confidence": ConfidenceLevel.HIGH,
                "matches": defs
            }

        # Multiple candidates -> AMBIGUOUS
        return {
            "status": "AMBIGUOUS",
            "symbol_name": query,
            "confidence": ConfidenceLevel.MEDIUM,
            "matches": defs
        }
