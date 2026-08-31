# Engineering Planning Model

## 1. Plan Structure
`EngineeringPlan` instances contain ordered `EngineeringPlanStep` items created deterministically from `TaskClassification` and `RepositorySnapshot` inputs.

## 2. Risk & Blast-Radius Calculation
Risk levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) are derived directly from `ImpactAnalyzer.analyze_impact()` blast-radius scores.
Plans with `MEDIUM`, `HIGH`, or `CRITICAL` risk automatically flag `approval_required = True`.
