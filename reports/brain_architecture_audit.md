# 🧠 Engineering Brain Architecture Audit

## 1. Existing Systems Analysis

### Memory Systems (`project_creator/learning/memory_db.py`)
- **CodingMemory (SQLite)**: Stores patterns, snippets, user styles, heuristics, git commits, and failures.
- **VectorStore (FAISS)**: Provides semantic search over snippets and failure contexts.
- **Current State**: Fragmented. Data is stored across multiple tables but lacks a cohesive "Brain" interface.

### Learning Systems (`project_creator/learning/`)
- **Learners**: `PatternLearner`, `RepoLearner`, `CommitLearner`, `FailureLearner`, `CorrectionLearner`, `SelfPlayEngine`.
- **Current State**: Distributed. Learners publish/subscribe via an `EventBus`.

### Retrieval Systems (`project_creator/memory/retriever.py`)
- **Retriever**: Merges SQL frequency-based patterns with VectorStore semantic results.
- **Current State**: Integrated directly into `Planner` and `Coder` agent prompts.

### Repair Systems (`project_creator/core/orchestrator.py`)
- **Repair Loop**: Critique → Sandbox → RepairAgent.
- **Current State**: Utilizes `Retriever.augment_prompt` to inject historical context during repair.

### Planner Systems (`project_creator/agents/planner_agent.py`)
- **Planner**: Generates initial multi-file blueprint.
- **Current State**: Uses basic prompt augmentation.

## 2. Identified Risks

### Duplication Risks
- `brain/repair_memory.py` vs existing `failures` table and `RepairAgent` context.
- `brain/architecture_memory.py` vs existing `patterns` (architecture type).
- `brain/semantic_search.py` vs existing `memory/vector_store.py`.

### Integration Points
- **Orchestrator**: Needs to invoke `Brain` before `Planner` to generate a `Strategy Document`.
- **Learners**: Need to feed higher-level abstractions into the `Brain` layer.

## 3. Recommended Brain Architecture

### Structure (`project_creator/brain/`)
- `engineering_brain.py`: Central orchestrator for all brain sub-modules.
- `strategy_builder.py`: Generates the "Strategy Document" using retrieved context.
- `repository_brain.py`: Specialized for cross-repo pattern extraction.
- `knowledge_graph.py`: Tracks relationships between frameworks, project types, and successful patterns.

### New Lifecycle
1. **User Goal** → `EngineeringBrain.consult()`
2. `EngineeringBrain` retrieves from `ArchitectureMemory`, `PatternMemory`, etc.
3. `StrategyBuilder` produces `Strategy Document`.
4. `Planner` generates `Blueprint` (Blueprint must align with Strategy).
5. `Coder` generates files (Coder must follow Strategy).
6. **Validation/Repair** → `Brain` records success/failure metrics.

## 4. Implementation Strategy

1. **Phase 1 (Repository Brain)**: Implement a deep scanner that identifies architectural boundaries.
2. **Phase 2 (Structured Memories)**: Create higher-level wrappers around `CodingMemory` for Repair, Pattern, and Architecture.
3. **Phase 3 (Strategy Builder)**: Implement the reasoning step that produces the observable Strategy Document.
4. **Phase 4 (Loop Closure)**: Connect the `Orchestrator` apply phase to the `Brain` for metric recording.
