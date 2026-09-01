# Semantic Trust Model

## 1. Overview
The **Semantic Trust Model** (`repository/semantic/trust/`) quantifies the trustworthiness of static analysis findings prior to autonomous code modification.

## 2. Trust Hierarchy

1. **`VERIFIED`**: Exact definition & AST evidence verified through tests or explicit human approval.
2. **`HIGH_CONFIDENCE`**: Unambiguous AST definition and exact import resolution (Score: 0.85 – 1.0). Allows autonomous execution.
3. **`PARTIAL`**: Cross-module naming match or structural path convention (Score: 0.50 – 0.84). Requires explicit approval.
4. **`LOW_CONFIDENCE`**: Heuristic name match or dynamic construct present (Score: 0.20 – 0.49). Requires discovery (`REQUIRES_DISCOVERY`).
5. **`UNKNOWN`**: Unresolved symbol or unparseable source syntax (Score: 0.0). Blocks autonomous modification (`REQUIRES_DISCOVERY`).
6. **`UNTRUSTED`**: Malicious, corrupted, or invalid graph state. Operations fail closed.
