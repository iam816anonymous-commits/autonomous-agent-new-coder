# 🎯 Deterministic Task Classifier (Phase C)

## Overview
Phase C introduces the **Deterministic Task Classifier** (`engine.classifier`). It translates natural language software engineering requests into strongly-typed `TaskClassification` structures containing task types, rule-based confidence scores, extracted parameters, evidence, required capabilities, and risk assessments—**100% offline without LLM dependencies**.

## Architecture & Pipeline

```text
Request Text
      │
      ▼
Vague/Negation Checks
      │
      ▼
Composite Request Detector ──► Split into subtasks if multiple operations
      │
      ▼
Rule Registry ───────────────► SymbolRenameRule, DependencyUpgradeRule, RouteExtensionRule, etc.
      │
      ▼
Repository Verification ─────► Verify symbol/file existence in Phase A RepositorySnapshot
      │
      ▼
TaskClassification ─────────► Typed Result (TaskType, confidence, parameters, capabilities, risk)
```

## Supported Task Types
- `SYMBOL_RENAME`: Extract `old_name`, `new_name`.
- `DEPENDENCY_UPGRADE`: Extract `package`, `target_version`.
- `DEPENDENCY_CHANGE`: Extract `operation` (`add`, `remove`, `replace`), `package`, `replacement`.
- `FILE_MOVE`: Extract `source`, `destination`.
- `CRUD_EXTENSION`: Extract `resource`.
- `ROUTE_EXTENSION`: Extract `http_method`, `route`, `resource`.
- `CODE_FORMATTING`: General formatting tasks.
- `TEST_REPAIR`: Repair failing test suites.
- `MIGRATION`: Extract `from_framework`, `to_framework`.
- `TEMPLATE_GENERATION`: Project template generation.
- `DOCUMENTATION_UPDATE`: Documentation and README updates.
- `ANALYSIS_ONLY`: Informational questions or repository analysis requests.
- `COMPOSITE_TASK`: Multi-task composite requests.
- `AMBIGUOUS`: Vague requests ("fix this project") or negated constraints ("don't upgrade").
- `UNSUPPORTED`: Unrecognized requests.

## Rule-Based Confidence & Evidence
- **0.90 – 1.00**: Strongly classified with explicit syntax matches.
- **0.70 – 0.89**: Likely classified (e.g. symbol rename where target symbol is not found in repository index).
- **0.50**: Ambiguous / Vague request requiring clarification.
- **0.00**: Unsupported / Unrecognized.

Every classification records explicit string `evidence` explaining why the rule matched and why the confidence level was assigned.

## Debug CLI Examples

```bash
# Classify a symbol rename request
python -m engine.cli classify "Rename calculate_total to calculate_invoice_total"

# Repository-aware classification
python -m engine.cli classify "Rename add to sum_numbers" --root /path/to/repo

# Classify composite request
python -m engine.cli classify "Upgrade React to 19 and rename calculateTotal to calculateInvoiceTotal"
```
