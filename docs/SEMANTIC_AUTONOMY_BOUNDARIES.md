# Semantic Autonomy Boundaries

## 1. Trust-Aware Planning Policy
The engineering planner enforces explicit trust boundaries before generating execution plans:
* `HIGH_CONFIDENCE` / `VERIFIED`: Autonomous operator proposal & execution permitted.
* `PARTIAL`: Requires explicit human approval.
* `LOW_CONFIDENCE` / `UNKNOWN`: Requires discovery mode (`REQUIRES_DISCOVERY`).
* `UNTRUSTED`: Operation rejected / fails closed.
