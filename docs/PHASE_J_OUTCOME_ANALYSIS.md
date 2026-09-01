# Outcome Analysis

## 1. Expected vs Actual Comparison
`ChangeOutcomeAnalyzer` compares `SemanticRepositorySnapshot` before and after execution using `DifferentialSemanticAnalyzer`:
* Verifies expected files and symbols were modified.
* Detects `unexpected_symbols` or `architectural_violations` (e.g. pattern degrading to `UNKNOWN`).
* Returns `ChangeOutcome` with `match_status` (`MATCH`, `UNEXPECTED_CHANGE`, `VIOLATION`).
