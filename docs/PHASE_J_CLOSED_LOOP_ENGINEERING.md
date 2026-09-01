# Closed-Loop Engineering Pipeline

## 1. Closed-Loop Flow
```text
User Intent
    │
    ▼
Change Discovery Engine (Queries Semantic Graph)
    │
    ▼
Change Impact Analyzer (Direct, Transitive, Test & Boundary Impact)
    │
    ▼
Confidence Gating Engine (READY / REQUIRES_DISCOVERY / REQUIRES_CLARIFICATION)
    │
    ▼
Pre-Execution Validator (Asserts Files & Symbols)
    │
    ▼
Execution Boundary (Transactional Sandbox Copy)
    │
    ▼
Change Outcome Analyzer (Snapshot_Before vs Snapshot_After Comparison)
```
