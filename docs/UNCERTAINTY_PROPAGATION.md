# Uncertainty Propagation

## 1. Call Graph Uncertainty
`UncertaintyPropagator` traverses incoming call edges using bounded breadth-first search (depth $\le 5$). When a callee symbol's confidence is degraded to `LOW` or `UNKNOWN`, the caller's call edge confidence is automatically degraded from `HIGH` to `MEDIUM`.
