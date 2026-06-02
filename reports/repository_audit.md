# 🕵️ Mini Jules Repository Audit Report

## 1. Architecture Weaknesses & Technical Debt

### Tight Coupling
- **`Orchestrator` & `Brain`**: The `Orchestrator` is becoming a "God Class" (173 lines) with direct dependencies on almost every other module. It handles everything from requirement gathering to repair cycles.
- **Global State in `server.py`**: The FastAPI server relies on a `GlobalState` singleton, which makes parallel project management difficult and testing more complex.

### Duplicate Logic
- **JSON Extraction**: Found in `project_creator/core/utils.py` but frequently referenced or re-implemented across agents.
- **Database Connectivity**: `sqlite3.connect` is called 11 times across the codebase. There is no centralized DB connection pool or context manager, leading to potential "database is locked" errors during high-activity sessions (like Night Learning).
- **Safety Checks**: `is_safe` and path sanitization are implemented in both `Storage` and `ActivityCollector`, with slight variations.

### Large Files
- `orchestrator.py` (173 lines) - Needs decomposition into sub-orchestrators (e.g., `ValidationOrchestrator`).
- `memory_db.py` (155 lines) - Handles too many different schemas (Night Learning, Git, Heuristics).

## 2. Security Risks
- **Sandbox Whitelist**: The `ToolExecutor` whitelist is small, but `python3` execution can still bypass many restrictions if not carefully monitored.
- **Credential Storage**: While `LearningConstitution` scrubs secrets, there is no verification that the `VectorStore` doesn't inadvertently store embeddings of sensitive logic.

## 3. Maintenance Risks
- **Module Proliferation**: The addition of `brain/` alongside `learning/` and `memory/` has created overlapping responsibilities. For example, `RepairMemory` (Brain) wraps `failures` (SQL), which is also used by `FailureLearner`.
- **Test Coverage**: While basic E2E and unit tests exist, there are no tests for the new `Brain` components (`OSLearner`, `StrategyBuilder`).

## 4. Performance Bottlenecks
- **Synchronous Server**: The `server.py` is mostly synchronous, potentially blocking the UI during long-running generation or repair cycles.
- **Vector Search**: Using `all-MiniLM-L6-v2` locally is efficient, but re-indexing on every write without a batching strategy may slow down the agent during high-velocity coding.
