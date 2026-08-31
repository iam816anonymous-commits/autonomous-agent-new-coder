# Semantic Planning Model

## 1. Discovery Gate & Assumptions
`EngineeringPlanner` uses `SemanticResolver` during plan creation:
* If a target symbol is `AMBIGUOUS`, the planner fails closed with `REQUIRES_DISCOVERY`.
* If a target symbol is `UNRESOLVED`, the planner fails closed with `PlanningError("Symbol does not exist")`.
* Every step records affected symbols, affected files, and confidence levels.
