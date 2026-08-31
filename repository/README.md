# 🧠 Repository Knowledge Graph (Phase A)

The `repository` package provides a local-first, deterministic understanding of software repositories without relying on LLMs or external network services.

## 🚀 Key Modules

- **`models.py`**: Strongly typed data models (`RepositoryInfo`, `FileInfo`, `Symbol`, `SymbolReference`, `DependencyEdge`, `DependencyGraphModel`, `ImpactReport`).
- **`scanner.py`**: Static directory walker that detects languages (Python, JS, TS, Java, Go, Rust, C#), frameworks (FastAPI, Flask, Django, React, Angular, Vue, Express, Next.js, Spring), package managers, entry points, and test files.
- **`symbols.py`**: AST-based symbol indexer for Python (functions, classes, methods, imports, calls) and regex/pattern matcher for JS/TS.
- **`dependency_graph.py`**: Static file dependency graph builder, circular dependency path detector, topological sorter, and unresolved import tracker.
- **`impact_analysis.py`**: Calculates direct/transitive dependents, related symbols, related tests, and deterministic blast-radius scores (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **`scan.py`**: High-level facade (`RepositoryAnalyzer.analyze(root)`) and debug CLI tool (`python -m repository.scan <path>`).

## 🛠 Usage Example

```python
from repository.scan import RepositoryAnalyzer

snapshot = RepositoryAnalyzer.analyze("/path/to/repo")

# Repository info
print(snapshot.info.languages)
print(snapshot.info.frameworks)

# Symbol queries
print(snapshot.symbols.find_definitions("calculate_total"))
print(snapshot.symbols.get_callers("calculate_total"))

# Dependency graph queries
print(snapshot.graph.cycles)
print(snapshot.dep_builder.topological_order())

# Impact analysis
impact = snapshot.analyze_file_impact("services/user.py")
print(f"Blast radius: {impact.blast_radius} (Score: {impact.blast_radius_score})")
```

## 🔒 Security & Performance
- **Zero Shell Execution**: Pure static analysis; repository code is never executed.
- **Strict Boundary Enforcer**: All path operations check against repository root to prevent path traversal outside workspace.
- **100% Deterministic**: Operates offline without network calls or non-deterministic LLM generations.
