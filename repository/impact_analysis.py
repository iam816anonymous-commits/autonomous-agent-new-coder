from typing import List, Dict, Set
from .models import ImpactReport, BlastRadiusLevel, RepositoryInfo
from .symbols import SymbolIndexer
from .dependency_graph import DependencyGraphBuilder

class ImpactAnalyzer:
    """
    Calculates direct/transitive affected files, related symbols, related tests,
    and deterministic blast-radius scoring for code changes.
    """
    def __init__(self, root: str, symbol_indexer: SymbolIndexer, dep_builder: DependencyGraphBuilder):
        self.root = root
        self.symbols = symbol_indexer
        self.dep_builder = dep_builder

    def analyze_impact(self, modified_file: str, repo_info: RepositoryInfo) -> ImpactReport:
        direct_dependents = self.dep_builder.get_dependents(modified_file)

        # Transitive dependents via BFS
        transitive_dependents: Set[str] = set()
        queue = list(direct_dependents)
        visited = set(direct_dependents)

        while queue:
            curr = queue.pop(0)
            transitive_dependents.add(curr)
            for dep in self.dep_builder.get_dependents(curr):
                if dep not in visited and dep != modified_file:
                    visited.add(dep)
                    queue.append(dep)

        transitive_list = sorted(list(transitive_dependents - set(direct_dependents)))

        # Related symbols
        symbols_in_modified = self.symbols.get_symbols_in_file(modified_file)
        related_symbol_names = sorted(list(set(s.name for s in symbols_in_modified)))

        # Related tests
        related_tests = self.dep_builder.get_related_tests(modified_file)
        for d in direct_dependents:
            for t in self.dep_builder.get_related_tests(d):
                if t not in related_tests:
                    related_tests.append(t)
        related_tests = sorted(related_tests)

        # Check entry points affected
        affected_entry_points = [ep for ep in repo_info.entry_points if ep == modified_file or ep in direct_dependents or ep in transitive_dependents]

        # Check cycle involvement
        cycles = self.dep_builder.detect_cycles()
        in_cycle = any(modified_file in cycle for cycle in cycles)

        # Deterministic Blast Radius Scoring
        score = 0
        score += len(direct_dependents) * 2
        score += len(transitive_list) * 1
        score += len(related_symbol_names) * 1
        score += len(affected_entry_points) * 3
        if in_cycle:
            score += 5

        if score <= 3:
            level = BlastRadiusLevel.LOW
        elif score <= 10:
            level = BlastRadiusLevel.MEDIUM
        elif score <= 25:
            level = BlastRadiusLevel.HIGH
        else:
            level = BlastRadiusLevel.CRITICAL

        return ImpactReport(
            changed_file=modified_file,
            direct_dependents=sorted(direct_dependents),
            transitive_dependents=transitive_list,
            related_symbols=related_symbol_names,
            related_tests=related_tests,
            blast_radius=level,
            blast_radius_score=score
        )
