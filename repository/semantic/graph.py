from typing import List, Dict, Set, Optional, Tuple
from .models import SemanticSymbol, SemanticRelation, SymbolKind, SemanticRelationType, ConfidenceLevel

class SemanticRepositoryGraph:
    """
    In-memory deterministic semantic repository graph connecting symbols, relations, definitions, and calls.
    """
    def __init__(self):
        self.symbols: Dict[str, SemanticSymbol] = {}
        self.relations: List[SemanticRelation] = []
        self._outgoing: Dict[str, List[SemanticRelation]] = {}
        self._incoming: Dict[str, List[SemanticRelation]] = {}
        self._name_to_ids: Dict[str, List[str]] = {}

    def add_symbol(self, symbol: SemanticSymbol) -> None:
        self.symbols[symbol.symbol_id] = symbol
        if symbol.name not in self._name_to_ids:
            self._name_to_ids[symbol.name] = []
        if symbol.symbol_id not in self._name_to_ids[symbol.name]:
            self._name_to_ids[symbol.name].append(symbol.symbol_id)

    def add_relation(self, relation: SemanticRelation) -> None:
        self.relations.append(relation)
        src = relation.source_symbol_id
        tgt = relation.target_symbol_id

        if src not in self._outgoing:
            self._outgoing[src] = []
        self._outgoing[src].append(relation)

        if tgt not in self._incoming:
            self._incoming[tgt] = []
        self._incoming[tgt].append(relation)

    def get_symbol(self, symbol_id: str) -> Optional[SemanticSymbol]:
        return self.symbols.get(symbol_id)

    def find_symbols(self, name: str) -> List[SemanticSymbol]:
        ids = self._name_to_ids.get(name, [])
        return [self.symbols[sid] for sid in ids if sid in self.symbols]

    def find_definitions(self, name: str) -> List[SemanticSymbol]:
        syms = self.find_symbols(name)
        return [s for s in syms if s.symbol_kind != SymbolKind.IMPORT]

    def find_references(self, symbol_id: str) -> List[SemanticRelation]:
        return [r for r in self._incoming.get(symbol_id, []) if r.relation_type in (SemanticRelationType.CALLS, SemanticRelationType.REFERENCES, SemanticRelationType.IMPORTS)]

    def outgoing_relations(self, symbol_id: str) -> List[SemanticRelation]:
        return self._outgoing.get(symbol_id, [])

    def incoming_relations(self, symbol_id: str) -> List[SemanticRelation]:
        return self._incoming.get(symbol_id, [])

    def reachable_symbols(self, start_symbol_id: str, max_depth: int = 5) -> List[SemanticSymbol]:
        visited: Set[str] = set()
        queue: List[Tuple[str, int]] = [(start_symbol_id, 0)]
        reachable: List[SemanticSymbol] = []

        while queue:
            curr_id, depth = queue.pop(0)
            if curr_id in visited or depth > max_depth:
                continue
            visited.add(curr_id)

            if curr_id != start_symbol_id and curr_id in self.symbols:
                reachable.append(self.symbols[curr_id])

            for rel in self._outgoing.get(curr_id, []):
                if rel.target_symbol_id not in visited:
                    queue.append((rel.target_symbol_id, depth + 1))

        return sorted(reachable, key=lambda s: s.symbol_id)

    def affected_symbols(self, symbol_id: str) -> List[SemanticSymbol]:
        """Returns direct and transitive dependents (incoming relations)."""
        visited: Set[str] = set()
        queue: List[str] = [symbol_id]
        affected: List[SemanticSymbol] = []

        while queue:
            curr_id = queue.pop(0)
            if curr_id in visited:
                continue
            visited.add(curr_id)

            if curr_id != symbol_id and curr_id in self.symbols:
                affected.append(self.symbols[curr_id])

            for rel in self._incoming.get(curr_id, []):
                if rel.source_symbol_id not in visited:
                    queue.append(rel.source_symbol_id)

        return sorted(affected, key=lambda s: s.symbol_id)
