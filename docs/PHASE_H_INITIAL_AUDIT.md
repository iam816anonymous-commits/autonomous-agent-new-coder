# Phase H Initial Repository Audit: Semantic Repository Intelligence & Structural Planning

## Executive Summary
This document records the mandatory repository audit prior to building Phase H (**Semantic Repository Intelligence & Structural Planning**). Findings are categorized under **VERIFIED**, **REUSABLE**, **PARTIALLY_IMPLEMENTED**, **MISSING**, **RISK**, and **DO_NOT_DUPLICATE**.

---

## 1. Audit Categories & Findings

### 1.1 `repository/scanner.py`
* **VERIFIED**: Fast file discovery, language detection, test file identification, entry point heuristics, manifest parsing.
* **REUSABLE**: File tree walking and path safety checks (`_is_safe_path`).

### 1.2 `repository/symbols.py`
* **VERIFIED**: AST-based parsing for Python functions, classes, methods, imports, and calls. Regex-based parsing for JS/TS.
* **PARTIALLY_IMPLEMENTED**: Python AST analysis in Phase A captures basic function/class definitions and function calls, but lacks fully qualified symbol names, decorator relationships (`@app.get`), inheritance hierarchies, and explicit confidence scoring. JS/TS regex parsing lacks AST precision.
* **REUSABLE**: Python `ast` visitor patterns and symbol data representations.

### 1.3 `repository/dependency_graph.py` & `impact_analysis.py`
* **VERIFIED**: Dependency edge creation, cycle detection using DFS, topological sorting, and file-level blast radius scoring.
* **MISSING**: Symbol-level call graph resolution with confidence bounds, architecture boundary crossing checks (e.g. `API` → `SERVICE` → `REPOSITORY`), and assumption tracking.

### 1.4 `engine/orchestrator/planner.py`
* **VERIFIED**: Deterministic plan generation using classification and basic impact analysis.
* **MISSING**: Semantic evidence injection into plan steps, explicit assumption tracking, and `REQUIRES_DISCOVERY` planning mode when symbol targets are ambiguous or unknown.

---

## 2. Risk Mitigation Strategies

* **RISK**: Over-claiming call graph precision in dynamic Python environments. *Mitigation*: Categorize call resolution strictly into `HIGH` (unique local function), `MEDIUM` (unambiguous imported symbol), `LOW` (heuristic match), or `UNKNOWN` (dynamic dispatch).
* **RISK**: Performance degradation on large repositories during semantic indexing. *Mitigation*: Implement incremental snapshot updates (`IncrementalSemanticAnalyzer`) selectively updating stale files.
