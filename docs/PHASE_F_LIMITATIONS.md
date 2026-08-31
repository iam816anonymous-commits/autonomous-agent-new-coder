# Phase F Limitations & Honest Disclosure

## 1. Scope & Capabilities
* **Supported Operators**: Currently supports token-level symbol renaming (`SymbolRenameOperator`) and file moving (`FileMoveOperator`).
* **Multi-step Complex Replanning**: Replanning is bounded to deterministic parameter adjustments and proposal regenerations (`MAX_REPLAN_ATTEMPTS=1`). Complex multi-file refactoring recipes requiring novel code synthesis are intentionally deferred to future LLM integration phases.

## 2. Security Boundaries
* **Deterministic Pipeline**: Operates 100% offline without LLMs, internet connection, or external API keys.
* **Workspace Isolation**: Modifications occur inside isolated transaction copies, preventing corruption of the user's primary codebase during test failures.
