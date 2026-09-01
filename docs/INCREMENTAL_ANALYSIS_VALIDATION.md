# Incremental Analysis Validation

## 1. Divergence Detection
`IncrementalSemanticValidator` compares the output of `IncrementalSemanticAnalyzer` against a full ground-truth `SemanticSnapshotter` rebuild. If any symbol ID divergence is detected, the engine discards incremental results and falls back to full re-analysis.
