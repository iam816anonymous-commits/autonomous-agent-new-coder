# 🏛️ Repository Intelligence & Knowledge Graph Specification

## Overview
Phase A of Mini-Jules introduces a deterministic **Repository Knowledge Graph** layer. This layer replaces non-deterministic LLM-based repository reasoning with exact static analysis algorithms.

## Architectural Pipeline
```text
Repository Path
      │
      ▼
RepositoryScanner ────────► Languages, Frameworks, Package Managers, Entry Points, Test Files
      │
      ▼
SymbolIndexer ───────────► Python AST & JS/TS Definitions, Imports, Calls, References
      │
      ▼
DependencyGraphBuilder ──► Static File Dependencies, Circular Cycles, Topological Sorter
      │
      ▼
ImpactAnalyzer ──────────► Direct & Transitive Dependents, Blast-Radius Score & Level
```

## Security Model
- **Static Analysis Only**: No subprocess execution of repository scripts, test runners, or installation hooks during repository analysis.
- **Safe Traversal**: Employs realpath boundary validation (`_is_safe_path`) to ensure operations remain strictly within the target repository workspace.

## Determinism Guarantee
Running `RepositoryAnalyzer.analyze(path)` multiple times against the same codebase produces byte-for-byte identical output.
