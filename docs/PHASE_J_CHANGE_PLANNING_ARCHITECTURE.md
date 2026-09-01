# Phase J Change Planning Architecture

## 1. Overview
The **Closed-Loop Semantic Change Planning Subsystem** (`engine/change_planning/`) transforms raw natural language engineering requests into evidence-backed, confidence-gated, and pre-execution verified change plans.

---

## 2. Subsystem Architecture

```text
engine/change_planning/
├── __init__.py
├── models.py            # ChangeRequest, ChangeStep, ChangePlan, PlanningStatus, ChangeOutcome
├── errors.py            # ChangePlanningError, DiscoveryError, PreExecutionAssertionError
├── discovery.py         # ChangeDiscoveryEngine (Investigates entry points, symbols, architecture)
├── impact.py            # ChangeImpactAnalyzer (Direct, transitive, test, and boundary impact)
├── gating.py            # ConfidenceGatingEngine (READY, REQUIRES_DISCOVERY, REQUIRES_CLARIFICATION, BLOCKED, HIGH_RISK)
├── pre_execution.py     # PreExecutionValidator (Pre-execution assertions prior to modification)
├── executor_contract.py # ChangeExecutorContract
└── outcome.py           # ChangeOutcomeAnalyzer (Expected vs Actual snapshot differencing)
```
