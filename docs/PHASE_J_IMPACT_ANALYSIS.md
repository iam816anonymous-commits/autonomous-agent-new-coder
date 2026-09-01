# Phase J Impact Analysis

## 1. Multi-Layer Impact Breakdown
`ChangeImpactAnalyzer` evaluates:
* **Direct Symbols**: Explicitly named target symbols.
* **Transitive Symbols**: Callers and dependents identified via `graph.affected_symbols()`.
* **Affected Tests**: Unit and integration test files depending on affected symbols.
* **Architectural Boundaries**: Layer crossings (`API_LAYER`, `SERVICE_LAYER`, `DATABASE_LAYER`).
