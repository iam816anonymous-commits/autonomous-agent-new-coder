# Semantic Analysis Threat Model

## 1. Threat Matrix

| Threat | Attack / Failure Vector | Impact | Detection | Mitigation | Residual Risk |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Incorrect Symbol Resolution** | Ambiguous class/function names across modules. | Modifying wrong symbol. | `SemanticResolver.resolve_definition` returns `AMBIGUOUS`. | Trigger `REQUIRES_DISCOVERY` gate. | None (fails closed). |
| **Dynamic Python Blind Spot** | Code uses `getattr()` or `eval()` to call methods. | Incomplete call graph. | `PythonDynamicDetector` AST scan. | Degrade trust level to `LOW_CONFIDENCE`. | None (automation blocked). |
| **Stale Semantic Graph** | File modified on disk after graph construction. | Operator applies stale edits. | `DifferentialSemanticAnalyzer` diff check. | Invalidate snapshot & trigger rebuild. | None. |
| **Incremental Divergence** | Partial re-parse misses transitive relations. | Stale relation edges. | `IncrementalSemanticValidator` full comparison. | Fallback to full rebuild on divergence. | None. |
| **Confidence Inflation** | Heuristic match marked as `HIGH` confidence. | Unsafe autonomous apply. | `ConfidenceCalibrator` factor scoring. | Strict evidence-based scoring rules. | None. |
