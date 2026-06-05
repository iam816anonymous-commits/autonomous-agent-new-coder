# 🏗️ Mini Jules: Architecture Overview

## The Orchestration Layer
Mini Jules operates as a **Coordinator-Specialist** system. The `Orchestrator` does not perform tasks itself; it delegates to three primary sub-coordinators:

1.  **GenerationCoordinator:** Handles the mapping of blueprints to actual source code.
2.  **ExecutionCoordinator:** Manages the interaction with the physical OS and toolchain.
3.  **ValidationManager:** Owns the feedback loop, deciding when a file is "Ready" or needs "Repair".

## The Intelligence Layer (Engineering Brain)
The `EngineeringBrain` is a stateless reasoning module that consumes stateful memory:
*   **Synthesis Logic:** Combines "Knowledge Cards" from diverse sources.
*   **Strategy Document:** A mandatory JSON/Markdown artifact that serves as the "Architectural North Star" for the duration of a project.

## The Memory Layer (Dual-Persistence)
*   **Relational (SQLite):** Used for **Exact Patterns**. ("Always use snake_case for functions").
*   **Semantic (FAISS):** Used for **Conceptual Patterns**. ("How did we fix a similar FastAPI authentication bug before?").

## The Feedback Loop (The "Golden Loop")
The core of Mini Jules's reliability is the **Verified Sandbox Mode**:
1.  **Generate:** Create file.
2.  **Test:** Run ruff/pytest in isolated venv.
3.  **Repair:** If fail, feed stderr to `RepairStrategist`.
4.  **Retest:** Repeat until pass or max cycles reached.

---
*Refers to implementation as of v14.1.0*
