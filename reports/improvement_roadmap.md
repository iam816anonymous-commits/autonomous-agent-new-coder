# 🗺️ Mini Jules Improvement Roadmap

Prioritized engineering tasks to evolve Mini Jules into a world-class autonomous agent.

## 🚀 Tier 1: Core Intelligence (High ROI)

### 1. Decouple Orchestrator (Impact: High | Complexity: Medium)
- Extract `ValidationManager` and `RepairStrategist` from `Orchestrator.py`.
- Purpose: Reduce God-class complexity and improve unit testability.

### 2. AST-Based Impact Analysis (Impact: High | Complexity: High)
- Implement `CallGraphLearner` to map cross-file dependencies.
- Purpose: Prevent regression errors by identifying all impacted files before generating a patch.

### 3. Hierarchical Planning (Impact: Medium | Complexity: Medium)
- Update `PlannerAgent` to produce a nested blueprint (Modules -> Phases -> Files).
- Purpose: Enable generation of 20+ file projects without architectural drift.

## 🛠️ Tier 2: Reliability & DX

### 1. Centralized DB Context Manager (Impact: Medium | Complexity: Low)
- Create `project_creator.core.database` to manage all SQLite interactions.
- Purpose: Eliminate "Database is locked" issues and reduce duplicate code.

### 2. Sandbox Virtual Environments (Impact: High | Complexity: High)
- Use `venv` or `uv` to create isolated environments for each project dry-run.
- Purpose: Allow Jules to test third-party dependencies without polluting the host.

## 📈 Success Metrics for Roadmap
- **Completion Rate**: Increase from 75% to 90% for multi-module projects.
- **Repair Latency**: Reduce repair cycles by 30% via better impact analysis.
- **Maintainability Index**: Reduce average function length in `core/` by 40%.
