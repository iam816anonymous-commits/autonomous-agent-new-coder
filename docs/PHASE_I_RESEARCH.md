# Phase I Research: Semantic Validation & Trust Calibration

## 1. Executive Summary
Phase I bridges the gap between static analysis and trustworthy autonomous execution. It establishes formal trust boundaries, evidence tracking, graph validation, differential comparison, dynamic Python detection, and uncertainty propagation.

---

## 2. Primary Architectural Principles

### 2.1 Soundness vs Completeness in Static Analysis
* **FACT**: Static analysis for dynamic languages (e.g. Python) cannot be simultaneously complete and sound for all edge cases (Rice's Theorem).
* **DESIGN DECISION**: Mini-Jules prioritizes **soundness and safety over completeness**. When static analysis cannot resolve a dynamic call or import, the engine explicitly reports `UNKNOWN` or `LOW_CONFIDENCE` rather than guessing.

### 2.2 Dynamic Behavior Detection & Trust Degradation
* **FACT**: Constructs such as `getattr(obj, attr_name)`, `eval()`, `exec()`, `importlib.import_module()`, and `from module import *` obscure static symbol visibility.
* **DESIGN DECISION**: `PythonDynamicDetector` identifies dynamic patterns, logs evidence, and downgrades the symbol/file trust level to `LOW_CONFIDENCE` or `UNTRUSTED`.

### 2.3 Bounded Uncertainty Propagation
* **FACT**: If function $A$ calls function $B$, and $B$'s definition or call resolution has `LOW_CONFIDENCE`, $A$'s call site confidence must also be degraded.
* **DESIGN DECISION**: `UncertaintyPropagator` traverses incoming call edges using bounded graph search (depth $\le 5$) to propagate confidence reductions without infinite loops.

---

## 3. Trust Boundary Matrix

| Semantic Trust Level | Autonomous Modification Allowed | Approval Requirement | Discovery Gate Required |
| :--- | :---: | :---: | :---: |
| **`VERIFIED`** | Yes | Configurable | No |
| **`HIGH_CONFIDENCE`** | Yes | Low/Medium Risk Policy | No |
| **`PARTIAL`** | Limited | Explicit Human Approval | No |
| **`LOW_CONFIDENCE`** | No | Blocked | Yes (`REQUIRES_DISCOVERY`) |
| **`UNKNOWN`** | No | Blocked | Yes (`REQUIRES_DISCOVERY`) |
| **`UNTRUSTED`** | No | Blocked / Reject | Yes (`FAIL_CLOSED`) |
