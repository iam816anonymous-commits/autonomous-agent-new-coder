from typing import Dict, Any, List
from repository.semantic.graph import SemanticRepositoryGraph
from repository.semantic.resolver import SemanticResolver

class SemanticAssertions:
    """
    Exposes deterministic semantic assertions for workflow planning and verification.
    """
    def __init__(self, graph: SemanticRepositoryGraph):
        self.graph = graph
        self.resolver = SemanticResolver(graph)

    def assert_symbol_exists(self, symbol_name: str) -> Dict[str, Any]:
        res = self.resolver.resolve_definition(symbol_name)
        passed = res["status"] in ("RESOLVED", "AMBIGUOUS")
        return {
            "assertion": "ASSERT_SYMBOL_EXISTS",
            "passed": passed,
            "symbol_name": symbol_name,
            "status": res["status"]
        }

    def assert_symbol_unique(self, symbol_name: str) -> Dict[str, Any]:
        res = self.resolver.resolve_definition(symbol_name)
        passed = res["status"] == "RESOLVED"
        return {
            "assertion": "ASSERT_SYMBOL_UNIQUE",
            "passed": passed,
            "symbol_name": symbol_name,
            "status": res["status"],
            "match_count": len(res.get("matches", []))
        }

    def assert_no_unresolved_calls(self) -> Dict[str, Any]:
        unresolved = [r for r in self.graph.relations if r.target_symbol_id.startswith("call:") and r.target_symbol_id not in self.graph.symbols]
        return {
            "assertion": "ASSERT_NO_UNRESOLVED_CALLS",
            "passed": len(unresolved) == 0,
            "unresolved_call_count": len(unresolved)
        }
