import os
import sys
import json
import argparse
from dataclasses import asdict
from typing import Dict, Any

from .scanner import RepositoryScanner
from .symbols import SymbolIndexer
from .dependency_graph import DependencyGraphBuilder
from .impact_analysis import ImpactAnalyzer
from .models import RepositoryInfo, DependencyGraphModel, ImpactReport

class RepositorySnapshot:
    """
    High-level deterministic snapshot of a repository's structure, symbols, dependencies, and impact rules.
    Operates offline without LLMs or network access.
    """
    def __init__(self, root: str):
        self.root = os.path.realpath(os.path.abspath(root))
        self.scanner = RepositoryScanner(self.root)
        self.symbols = SymbolIndexer(self.root)
        self.dep_builder = DependencyGraphBuilder(self.root)

        self.info, self.file_info_map = self.scanner.scan()
        all_code_files = self.info.source_files + self.info.test_files

        self.symbols.index_repository(all_code_files)
        self.graph = self.dep_builder.build_graph(all_code_files)
        self.impact_analyzer = ImpactAnalyzer(self.root, self.symbols, self.dep_builder)

    def analyze_file_impact(self, modified_file: str) -> ImpactReport:
        return self.impact_analyzer.analyze_impact(modified_file, self.info)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "repository": asdict(self.info),
            "symbol_count": len(self.symbols.symbols),
            "reference_count": len(self.references_count_helper()),
            "dependency_graph": {
                "node_count": len(self.graph.nodes),
                "edge_count": len(self.graph.edges),
                "has_cycles": len(self.graph.cycles) > 0,
                "cycles": self.graph.cycles,
                "unresolved_imports": self.graph.unresolved_imports
            }
        }

    def references_count_helper(self):
        return self.symbols.references

class RepositoryAnalyzer:
    @staticmethod
    def analyze(root: str) -> RepositorySnapshot:
        return RepositorySnapshot(root)

def main():
    parser = argparse.ArgumentParser(description="Mini-Jules Deterministic Repository Knowledge Graph Scanner")
    parser.add_argument("path", nargs="?", default=".", help="Path to repository root")
    parser.add_argument("--symbols", action="store_true", help="Print indexed symbols")
    parser.add_argument("--dependencies", action="store_true", help="Print dependency graph details")
    parser.add_argument("--impact", type=str, help="Calculate impact for a modified file")

    args = parser.parse_args()

    snapshot = RepositoryAnalyzer.analyze(args.path)

    if hasattr(args, "subcommand") and args.subcommand == "semantic-analyze":
        from .semantic.snapshot import SemanticSnapshotter
        sem_snap = SemanticSnapshotter.capture(snapshot)
        res = {
            "fingerprint": sem_snap.repository_fingerprint,
            "architecture": sem_snap.architecture,
            "symbol_count": len(sem_snap.graph.symbols),
            "relation_count": len(sem_snap.graph.relations)
        }
        print(json.dumps(res, indent=2))
        return

    if hasattr(args, "subcommand") and args.subcommand == "semantic-validate":
        from .semantic.snapshot import SemanticSnapshotter
        from .semantic.validation.validator import SemanticGraphValidator
        sem_snap = SemanticSnapshotter.capture(snapshot)
        validator = SemanticGraphValidator(sem_snap.graph)
        val_res = validator.validate()
        print(json.dumps(asdict(val_res), indent=2))
        return

    if args.impact:
        impact = snapshot.analyze_file_impact(args.impact)
        print(json.dumps(asdict(impact), indent=2))
    elif args.symbols:
        syms = [asdict(s) for s in snapshot.symbols.symbols]
        print(json.dumps(syms, indent=2))
    elif args.dependencies:
        deps = {
            "nodes": snapshot.graph.nodes,
            "edges": [asdict(e) for e in snapshot.graph.edges],
            "cycles": snapshot.graph.cycles,
            "unresolved_imports": snapshot.graph.unresolved_imports
        }
        print(json.dumps(deps, indent=2))
    else:
        print(json.dumps(snapshot.to_dict(), indent=2))

if __name__ == "__main__":
    main()
