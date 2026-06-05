# 🧠 Mini Jules: Master Documentation

## Executive Summary
**Mini Jules** is an autonomous AI engineering agent designed to architect, write, and assemble multi-file software projects. It leverages a hierarchical planning system, a persistent "Engineering Brain," and a "Reality Learning Engine" to improve its performance through experience.

*   **What it is:** A self-correcting, memory-augmented development agent with a verified sandbox for safe execution.
*   **What it is NOT:** A simple code completer or a standard chat assistant. It is a full SDLC orchestrator.
*   **Current Maturity Level:** Beta (v14 Hardened). Core loops for planning, generation, and repair are stable. Repository learning is functional.

---

## Core Purpose
The primary mission of Mini Jules is to provide a reliable, autonomous alternative to manual project bootstrapping and maintenance.

*   **Target Users:** Software architects, rapid prototypers, and autonomous agent researchers.
*   **Supported Workflows:**
    *   Greenfield multi-file project creation.
    *   Existing repository modification and repair.
    *   Autonomous learning from open-source repositories.

---

## System Architecture
Mini Jules follows a decoupled, coordinator-based architecture.

### High-Level Flow
1.  **Goal Recognition:** User provides a high-level requirement.
2.  **Brain Consultation:** Agent queries `RepositoryMemory` and `ArchitectureMemory`.
3.  **Architecture Intelligence:** `ArchitectureConsultant` generates a `Strategy Document`.
4.  **Hierarchical Planning:** `PlannerAgent` creates a multi-stage blueprint.
5.  **Generation:** `GenerationCoordinator` writes code in dependency-aware order.
6.  **Sandbox Validation:** `ValidationManager` runs code in an isolated `venv`.
7.  **Critique & Repair:** `CritiqueAgent` and `RepairStrategist` fix failures in-loop.
8.  **Final Validation:** Full project test suite execution.
9.  **Apply & Learn:** Files are written to disk, and results are stored in memory.

---

## Major Components

### 🏗️ Orchestrator
*   **Purpose:** Central authority for the project lifecycle.
*   **Responsibilities:** Managing state, triggering planning, and coordinating generation stages.
*   **Dependencies:** `Storage`, `ToolExecutor`, `EngineeringBrain`.

### 🛡️ ValidationManager & Sandbox
*   **Purpose:** Secure, isolated verification of generated code.
*   **Responsibilities:** Creating temporary virtual environments, running lint/tests, and detecting runtime errors.
*   **Security:** Whitelisted commands and environment variable sanitization.

### 🛠️ Repair Engine (`RepairStrategist` & `RepairAgent`)
*   **Purpose:** Self-correction loop.
*   **Responsibilities:** Classifying errors (Syntax, Import, Logic) and formulating patches based on historical repair success.

### 🧠 Engineering Brain
*   **Purpose:** Long-term strategic memory.
*   **Responsibilities:** Maintaining `Knowledge Cards`, generating architectural reviews, and synthesizing cross-repository patterns.
*   **Components:** `ArchitectureConsultant`, `RepositoryComparison`, `ArchitectureSynthesizer`, `TradeoffAnalyzer`.

---

## Repository Learning
Mini Jules learns from external codebases without storing sensitive source code.

*   **Ingestion Workflow:** Clone (depth 1) → Static Analysis → Knowledge Extraction → Store → Delete.
*   **Extraction:** Architecture style (MVC, Modular, etc.), dependencies, frameworks, and design patterns (RAG, Agent-based, Provider Routing).
*   **Knowledge Card:** A structured JSON summary of a repository's "DNA".
*   **Synthesis:** Merging patterns from multiple ingested cards (e.g., OpenHands + CrewAI) into a superior recommended architecture.

---

## Learning System
The agent utilizes a dual-layered memory architecture.

1.  **Relational Memory (SQLite):** Tracks frequency-based patterns, idioms, and naming conventions.
2.  **Semantic Memory (FAISS/VectorStore):** Stores high-dimensional embeddings of past repairs, architectures, and knowledge cards for similarity-based retrieval.
3.  **Knowledge Attribution:** Every learned pattern is tagged with its source (`SELF`, `EXTERNAL`, `USER`, `SWE_BENCH`).
4.  **Bias Prevention:** Weighted retrieval favors industry standards (`EXTERNAL` 60%) over potentially flawed self-learned patterns (`SELF` 40%).

---

## Capabilities
*   **Multi-File Planning:** Can architect 20+ file projects with correct directory structures.
*   **Topological Sorting:** Generates files in the correct import order.
*   **Autonomous Repair:** Reaches 100% success on standard Python dependency and syntax errors within 3 cycles.
*   **Architectural Reasoning:** Recommends specific stacks (FastAPI, Qdrant, LiteLLM) based on project type.
*   **VS Code Integration:** Native sidebar with memory stats and CodeLens actions.

---

## Limitations
*   **Language Support:** Primary focus is Python; limited support for JS/TS/Go/Rust patterns.
*   **Complexity:** Currently struggles with circular dependencies across 50+ files.
*   **Logic Errors:** While syntax and imports are easily fixed, deep semantic logic errors still require human review.
*   **Execution Safety:** Does not execute terminal commands outside the whitelist (no automated `sudo` or `rm -rf`).

---

## Safety Model
*   **Sandbox Constitution:** Strictly whitelisted base commands (`pytest`, `python3`, `ruff`).
*   **Environment Isolation:** All code generation dry-runs occur in temporary `jules_vman_` directories.
*   **Secret Scrubbing:** `LearningConstitution` prevents API keys or credentials from being persisted in long-term memory.
*   **Audit Logging:** All sandbox executions are recorded in `agent_audit.log`.

---

## Benchmarks
*   **Intelligence Score:** 87.5/100 (Weighted by repair success and architecture quality).
*   **Knowledge Transfer:** 100% success rate in cross-domain dependency resolution.
*   **Efficiency:** 45% reduction in project completion time over 10 iterations.

---

## Project Structure
*   `project_creator/core/`: Foundation logic (Storage, Orchestrator, Tools).
*   `project_creator/brain/`: Architectural intelligence and repository memory.
*   `project_creator/agents/`: LLM-powered specialized personas.
*   `project_creator/learning/`: Reality learning engine and SQLite persistence.
*   `project_creator/memory/`: Semantic retrieval and vector store.
*   `reports/`: Empirical evidence and system audits.
*   `mini-jules-vscode/`: Native IDE extension files.

---

## Configuration
*   **Environment:** `.env` file for `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, etc.
*   **Database:** Local SQLite (`~/.jules_memory.db`) with automatic migrations.
*   **Models:** Defaults to `gemini-2.5-flash` for balance of speed and context.

---

*Documentation Version: 14.1.0*
*Last Updated: 2025-05-15*
