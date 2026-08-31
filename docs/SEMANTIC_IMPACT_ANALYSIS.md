# Semantic Impact Analysis

## 1. Direct & Transitive Reachability
Semantic impact analysis uses `SemanticRepositoryGraph.affected_symbols()` to trace callers and dependents across AST call graphs.
Blast-radius scoring incorporates both file dependents and architectural boundary crossings (e.g., modifying a database model referenced in API routes).
