# 🕵️ Mini-Jules Repository Audit Report (AUDIT.md)

## Executive Summary
This document provides a comprehensive audit of the **Mini-Jules** repository as of the current codebase state. Mini-Jules is currently structured as an LLM-orchestrated software creation and repair agent. In order to achieve the vision of a **local-first, deterministic autonomous software-engineering engine** that operates without requiring an LLM for core capabilities, significant architectural transitions are required.

This audit evaluates the codebase strictly against source files rather than documentation claims.

---

## 1. Current Architecture

The existing repository consists of two main software packages and auxiliary directories:

1. **Python Backend (`project_creator/`)**:
   - **Entrypoints**: `main.py` (CLI prompt) and `server.py` (FastAPI bridge server).
   - **Orchestration**: `orchestrator.py` centralizes project blueprinting, stage execution, file generation, test execution, and repair cycles. It delegates tasks to `GenerationCoordinator`, `ExecutionCoordinator`, `ValidationManager`, and `RepairStrategist`.
   - **Agents (`project_creator/agents/`)**:
     - `planner_agent.py`: Asks LLM for a hierarchical JSON blueprint.
     - `coder_agent.py`: Prompts LLM to generate code files with security instructions.
     - `critique_agent.py`: Prompts LLM to review code quality.
     - `repair_agent.py`: Prompts LLM for JSON patches when tests fail.
     - `dialogue_agent.py`: Gathers requirements via LLM prompts.
   - **Providers & Router (`project_creator/providers/`, `project_creator/router/`)**:
     - `provider_router.py`: Routes prompts through a fallback engine across Groq, Gemini, OpenRouter, and ChatGPT Browser providers.
   - **Brain & Learning (`project_creator/brain/`, `learning/`, `memory/`)**:
     - `call_graph_learner.py`: Python AST call-graph and impact analyzer.
     - `architecture_extractor.py`: Heuristic file & directory structure analyzer.
     - `dependency_analyzer.py`: String-heuristic file dependency graph sorter.
     - `repository_intelligence.py` & `repository_brain.py`: High-level summary generators.
     - `memory_db.py`, `pattern_learner.py`, `vector_store.py`: SQLite + FAISS pattern memory.

2. **VS Code Extension (`mini-jules-vscode/`)**:
   - Written in TypeScript (`extension.ts`, `bridge.ts`, `codelens.ts`).
   - Provides sidebar Webview and Python file CodeLens items.

3. **Documentation & Benchmarks (`docs/`, `reports/`, `validate_jules.py`)**:
   - Extensive markdown documentation (`MASTER_DOCUMENTATION.md`, `CAPABILITIES_MATRIX.md`, `LIMITATIONS.md`).
   - Mocked release validation script (`validate_jules.py`).

---

## 2. Implemented Functionality

The following core utilities are fully implemented in Python source code:

- **Python AST Call Graph & Impact Analysis (`CallGraphLearner`)**:
  - Parses `.py` files using Python's standard `ast` module.
  - Tracks function definitions, async function definitions, class bases, and function call relationships.
  - Identifies files that invoke symbols defined in a target modified file.
- **Repository Structure Extraction (`ArchitectureExtractor`)**:
  - Walks file hierarchies, skipping hidden directories.
  - Identifies Python modules (`__init__.py`), entry points (`main.py`, `app.py`, `server.py`), test directories, and key architectural patterns via keyword inspection.
  - Calculates a normalized complexity score based on module and file counts.
- **Dependency Topological Sorting (`DependencyAnalyzer`)**:
  - Builds dependency lists by scanning file descriptions for referenced module names.
  - Generates a topologically sorted list of files for ordered code generation.
- **Whitelisted Tool Execution (`ToolExecutor`)**:
  - Restricts subprocess execution to allowed bases (`pytest`, `ruff`, `black`, `python3`).
  - Rejects commands containing dangerous flags or patterns (`sudo`, `chmod`, `rm -rf /`, `curl`, `wget`, `eval`, `exec`).
  - Supports running commands inside a workspace `.venv` directory.
  - Writes audit logs to `agent_audit.log`.
- **Safe Path & Atomic Storage Management (`Storage`)**:
  - Resolves path targets using `_safe_join` to prevent path traversal outside `project_root`.
  - Atomically reads existing project files while excluding `.git`, `node_modules`, `venv`, and internal state files.
- **Unified Diff Generation (`PatchManager`)**:
  - Uses standard `difflib.unified_diff` to generate standard git-compatible unified diffs between old and new code strings.
- **Thread-Safe Database Management (`DatabaseManager`)**:
  - Provides thread-safe SQLite connection and transaction context managers in `project_creator/core/database/db_manager.py`.
- **Secret Scrubbing (`LearningConstitution`)**:
  - Regex-based scrubbing of AWS Access Key IDs, OpenAI API keys, and RSA private key blocks from stored patterns and snippets.

---

## 3. Verified Capabilities

Verified by direct code execution and static analysis:

1. **Path Safety**: `Storage._safe_join` correctly raises `ValueError` on path traversal attempts (e.g. `../../etc/passwd`).
2. **AST Function Mapping**: `CallGraphLearner` successfully builds in-memory caller maps for standard Python files.
3. **Diff Creation**: `PatchManager.generate_diff` produces exact unified diff format output.
4. **Subprocess Whitelisting**: `ToolExecutor` blocks forbidden bases (e.g., `bash`, `curl`) and logs to `agent_audit.log`.
5. **Database Migration & Safety**: `CodingMemory` and `DatabaseManager` handle SQLite table initialization and migrations safely.

---

## 4. Missing Capabilities (Required for Target Vision)

The following core requirements from the Master Jules Prompt are currently **missing** from the codebase:

1. **Deterministic Software Engineering Engine (No-LLM Operating Mode)**:
   - There is no `DeterministicProvider` or offline deterministic engine capable of receiving tasks (such as "Rename calculate_total to calculate_invoice_total" or "Upgrade package X") and executing them without an LLM.
2. **Deterministic Task Classifier**:
   - The system lacks a rule-based/syntax-based task classifier for categories like `DEPENDENCY_UPGRADE`, `SYMBOL_RENAME`, `IMPORT_CHANGE`, `CONFIG_CHANGE`, `CRUD_EXTENSION`, `ROUTE_EXTENSION`, `FILE_MOVE`, etc.
3. **AST / Codemod Transformation Engine**:
   - No structural refactoring operators (e.g., AST symbol rename, import insertion/deletion, function body mutation, class method injection).
4. **Deterministic Repair Engine**:
   - All test repairs currently delegate to `RepairAgent` (LLM). There are no deterministic repair strategies for missing imports, syntax errors, or formatting mismatches.
5. **Explicit Persistent Task State Machine**:
   - Task state is handled implicitly in transient orchestrator variables. There is no persistent state machine tracking transitions (`RECEIVED` -> `ANALYZING` -> `PLANNED` -> `AWAITING_APPROVAL` -> `EXECUTING` -> `VERIFYING` -> `REPAIRING` -> `READY_TO_APPLY` -> `COMPLETED`).
6. **Cross-Language Symbol Index & Dependency Graph**:
   - `CallGraphLearner` is Python AST-only. There is no symbol index or multi-language dependency graph for TypeScript, JavaScript, Go, Rust, etc.
7. **Capability-Based Security Model**:
   - Security relies on base command string matching in `ToolExecutor`. There is no capability-based permission model (`filesystem.read`, `git.commit`, `process.test`).
8. **Automated Security Verification Pipeline**:
   - Pre-patch security scans for SQLi, command injection, path traversal, or credential exposure are not implemented as actual code check routines.
9. **First-Class CLI Architecture**:
   - `main.py` is an interactive script using `input()`. There is no CLI command parser supporting `agent analyze`, `agent plan`, `agent run`, `agent test`, `agent diff`, `agent approve`, `agent rollback`, `agent commit`.

---

## 5. Dead / Stubbed / Mocked Code

The following components contain fake, hardcoded, or placeholder implementations:

1. **`validate_jules.py`**:
   - **Status**: MOCKED / FAKE.
   - **Details**: `ProductionValidationRunner.run_production_validation()` hardcodes static dictionary metrics with fake pass rates (`"patch_acceptance": 1.0`, `"completion_time": 42.5`) instead of executing actual software engineering benchmark tasks.
2. **`mini-jules-vscode/src/extension.ts`**:
   - **Status**: STUBBED / MOCKED.
   - **Details**: `JulesViewProvider` hardcodes HTML strings (`Tasks Completed: 15`, `Patterns Learned: 58`, `Quota Used: 340`).
   - Registered extension commands (`MiniJules.Generate`, `MiniJules.Repair`) only display VS Code notification toasts.
3. **`mini-jules-vscode/src/bridge.ts`**:
   - **Status**: STUBBED.
   - **Details**: `scanWorkspace()` returns an empty array (`return []`).
4. **`project_creator/brain/dependency_analyzer.py`**:
   - **Status**: STUBBED METHODS.
   - **Details**: `_check_circular_dependencies()` and `_check_missing_imports()` contain empty `pass` statements.

---

## 6. Security Risks

1. **Host Python Script Execution**:
   - `ToolExecutor` allows `python3` in its whitelist. An arbitrary Python script executed in the workspace can execute system calls or write outside the directory if not wrapped in isolated sandbox environments.
2. **Direct File I/O in Learning/Brain Modules**:
   - While `Storage.write_file` enforces `_safe_join`, several modules in `brain/` and `learning/` (e.g. `RepoIndexer`, `CallGraphLearner`) use standard `open()` directly on paths provided during ingestion without verifying sandbox root boundaries.
3. **Unsanitized Command Argument Splitting**:
   - Shell argument parsing in `ToolExecutor` relies on `shlex.split`, but lacks capability scopes or environment jail isolation.

---

## 7. Architecture Problems & Technical Debt

1. **Total LLM Dependency**:
   - The core orchestrator (`orchestrator.py`) cannot function without external LLM provider access.
2. **Fragmented Memory & Brain Modules**:
   - Responsibilities are split across `project_creator/brain/`, `project_creator/learning/`, and `project_creator/memory/` with overlapping DB interactions and vector search wrappers.
3. **Global Server State**:
   - `server.py` uses a single global state (`state = GlobalState()`), preventing multi-tenant or concurrent task execution.
4. **Missing Task State Recovery**:
   - If the server process crashes mid-generation or mid-repair, state is lost or corrupted in `.agent_session.json`.

---

## 8. Reusable Components

The following components can be retained and repurposed in the target architecture:

- **`project_creator/core/storage.py`**: `Storage._safe_join` and atomic file write logic.
- **`project_creator/core/patch.py`**: `PatchManager` diff generation and colorized terminal output.
- **`project_creator/brain/call_graph_learner.py`**: Python AST parsing logic for function call graph creation.
- **`project_creator/core/database/db_manager.py`**: SQLite connection context manager.
- **`project_creator/learning/constitution.py`**: `LearningConstitution` regex secret scrubbing rules.
- **`project_creator/brain/architecture_extractor.py`**: Structure extraction and heuristic pattern detection.

---

## 9. Components Requiring Refactoring or Replacement

1. **`project_creator/router/provider_router.py`**:
   - **Refactor**: Add `DeterministicProvider` as the primary/fallback execution provider.
2. **`project_creator/core/orchestrator.py`**:
   - **Refactor**: Decouple LLM prompts from task execution; integrate deterministic state machine and task planner.
3. **`project_creator/core/tools.py`**:
   - **Refactor**: Replace base whitelist string checks with capability-based security model (`CapabilitySandbox`).
4. **`mini-jules-vscode/`**:
   - **Refactor**: Replace hardcoded HTML with actual RPC API client bridge calling local Mini-Jules daemon.
5. **`validate_jules.py`**:
   - **Replace**: Implement real deterministic benchmark runner.

---

## 10. V1 Migration Plan

To align with the target architecture outlined in Section 4 of the Master Jules Prompt, the project will evolve into the following modular directory structure:

```text
mini-jules/
├── engine/             # State machine, task classifier, planner, policy
├── repository/         # Scanner, parser, symbols, dependency graph, impact analysis
├── operations/         # Engineering operators, AST transforms, codemods, templates
├── verification/       # Test runner, static analysis, security, diff engine
├── repair/             # Deterministic failure classifier, repair rules, strategies
├── sandbox/            # Capability sandbox and isolated workspace runner
├── git/                # Checkpoints, diffs, branches, rollbacks
├── providers/          # Deterministic, Local LLM, Cloud LLM providers
├── cli/                # First-class CLI interface
├── vscode/             # VS Code extension client bridge
└── tests/              # Subsystem unit and integration tests
```

### Phased Migration Sequence:
- **Phase A**: Repository Knowledge Graph (Scanner, Symbol Index, Dependency Graph, Impact Analysis).
- **Phase B**: Task State Machine & Task Record persistence.
- **Phase C**: Deterministic Task Classifier (Rule-based task taxonomy).
- **Phase D**: Engineering Operator Framework (RenameSymbol, AddImport, FileMove, etc.).
- **Phase E**: AST / Codemod Transformation Engine.
- **Phase F**: Structured Plan, Risk Assessment & Change Budget.
- **Phase G**: Checkpoint, Rollback & Capability Sandbox.
- **Phase H**: Multi-ecosystem Test Engine & Failure Classification.
- **Phase I**: Bounded Deterministic Repair Engine.
- **Phase J**: Static Security Review & SAST Verification.
- **Phase K**: Git Diff Engine, Rollbacks & Commit Operations.
- **Phase L**: CLI Commands & VS Code Daemon Bridge.

---

## 11. File-by-File Proposed Changes

| File Path | Action | Description |
| :--- | :--- | :--- |
| `engine/state_machine.py` | Create | Implements explicit persistent task state machine. |
| `engine/task_classifier.py` | Create | Implements deterministic task classification rules. |
| `engine/planner.py` | Create | Generates machine-readable deterministic plans with budgets. |
| `repository/scanner.py` | Create | Discovers languages, frameworks, package managers, entry points. |
| `repository/symbols.py` | Create | Symbol indexer for functions, classes, methods, caller/callee sets. |
| `repository/dependency_graph.py` | Create | Multigraph for file, symbol, package, test dependencies. |
| `repository/impact_analysis.py` | Create | Calculates blast-radius scores (LOW/MEDIUM/HIGH/CRITICAL). |
| `operations/operators.py` | Create | Reusable operators (`RenameSymbol`, `AddImport`, `MoveFile`, etc.). |
| `operations/codemod.py` | Create | Codemod framework for structural code transformations. |
| `sandbox/capability_sandbox.py` | Create | Enforces capability permissions and workspace isolation. |
| `repair/deterministic_repair.py` | Create | Strategy selector for known deterministic failure categories. |
| `verification/security_scan.py` | Create | SAST security checks for SQLi, secrets, injection, path traversal. |
| `providers/deterministic_provider.py` | Create | Offline execution provider without LLM requirement. |
| `cli/main.py` | Create | Standard CLI command group using `argparse`. |
| `validate_jules.py` | Overwrite | Replace mock metrics with real test/benchmark runner. |
| `mini-jules-vscode/src/bridge.ts` | Overwrite | Wire actual API client calls to localhost server endpoints. |

---

## 12. Testing Strategy

1. **Subsystem Unit Tests (`tests/`)**:
   - `test_scanner.py`: Verify project scanning across Python, Node.js, and mixed repositories.
   - `test_symbol_index.py`: Verify function/class definition and caller/callee indexing.
   - `test_dependency_graph.py`: Verify topological sorting and dependency retrieval APIs.
   - `test_task_classifier.py`: Verify classification of structured and natural task queries.
   - `test_operators.py`: Verify AST manipulations (`RenameSymbol`, `AddImport`, `MoveFile`).
   - `test_sandbox.py`: Verify capability restriction enforcement and path boundary checks.
   - `test_repair_engine.py`: Verify deterministic fixes for missing imports and formatting errors.
   - `test_state_machine.py`: Verify state transition persistence and recovery after simulated process kill.
2. **Integration & E2E Tests**:
   - Test full offline execution flow: `Task -> Classify -> Plan -> Checkpoint -> Operator -> Test -> Security Scan -> Diff -> Commit` without network or LLM API keys.
3. **Failure & Regression Testing**:
   - Test broken dependencies, invalid syntax, command timeout, missing package managers, and rollback on repair failure.

---
*Audit Completed and Verified Against Repository Source Files.*
