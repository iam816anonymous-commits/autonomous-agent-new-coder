# Semantic Repository Architecture

## 1. Overview
The **Semantic Repository Intelligence Subsystem** (`repository/semantic/`) enhances Mini-Jules' structural understanding of code bases. It extracts symbol definitions, qualified names, AST call graphs, inheritance trees, route decorators, and architectural layer patterns without requiring an LLM.

---

## 2. Component Hierarchy

```text
repository/semantic/
├── __init__.py
├── models.py            # SemanticSymbol, SemanticRelation, SymbolKind, ConfidenceLevel, Evidence
├── errors.py            # SymbolResolutionError, AmbiguousSymbolError
├── graph.py             # SemanticRepositoryGraph (In-memory queryable graph)
├── resolver.py          # SemanticResolver (Definition & reference resolution)
├── python_analyzer.py   # PythonSemanticAnalyzer (Authoritative Python AST parser)
├── call_graph.py        # ConservativeCallGraph (Call confidence classification)
├── architecture.py      # ArchitectureDetector (Layered / MVC / Service-Repo boundary detection)
├── queries.py           # SemanticQueryEngine (who_calls, what_does_this_call, implementation_path)
├── confidence.py        # ConfidenceModel (HIGH, MEDIUM, LOW, UNKNOWN)
├── snapshot.py          # SemanticSnapshotter & SemanticRepositorySnapshot
└── incremental.py       # IncrementalSemanticAnalyzer
```
