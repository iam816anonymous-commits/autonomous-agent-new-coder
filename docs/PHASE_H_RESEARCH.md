# Phase H Research: Semantic Repository Intelligence

## 1. Architectural Guidance & Research Questions

### 1.1 What can Mini-Jules implement using Python standard library alone?
* **Python AST (`ast` module)**: Authoritative structural parser for Python files. Standard library `ast.NodeVisitor` extracts modules, classes, functions, methods, parameters, decorators, inheritance, assignments, and function call nodes cleanly without external tools.
* **Standard Library Graph Structs**: In-memory adjacency lists and sets handle graph queries (definitions, references, reachability, shortest paths) deterministically without external graph databases.

### 1.2 What semantic claims can safely be made vs. what must remain probabilistic?
* **VERIFIED FACT (High Confidence)**: AST definitions, module imports, exact local function calls, and explicit class inheritance.
* **HEURISTIC (Medium/Low Confidence)**: Method calls on dynamic objects (`obj.process()`), cross-language imports, or regex-based JS/TS declarations.
* **UNKNOWN**: Dynamic dispatch (`getattr`, `eval`), reflection, or runtime dependency injection. These are explicitly reported as `ConfidenceLevel.UNKNOWN`.

### 1.3 How does semantic intelligence improve engineering decisions?
* **Planner Operator Selection**: Explicitly identifies whether a target symbol is unique (`HIGH`), ambiguous (`AMBIGUOUS`), or missing (`REQUIRES_DISCOVERY`).
* **Impact Analysis & Risk**: Detects when a change crosses architectural boundaries (e.g. `API_ROUTE` → `SERVICE` → `DATABASE`) to assign blast-radius scores based on semantic risk rather than raw file count alone.
