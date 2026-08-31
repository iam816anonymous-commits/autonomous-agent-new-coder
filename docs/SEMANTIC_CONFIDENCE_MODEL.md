# Semantic Confidence Model

## 1. Evidence Rules
Confidence levels are strictly assigned based on extraction mechanisms:
* **`HIGH`**: Python AST definitions, unique import resolution.
* **`MEDIUM`**: Unambiguous name matches across modules, structural file conventions.
* **`LOW`**: Heuristic pattern matching.
* **`UNKNOWN`**: Unresolved dynamic imports, reflection, dynamic dispatch.
