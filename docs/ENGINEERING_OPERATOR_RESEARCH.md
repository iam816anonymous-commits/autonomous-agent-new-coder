# 🔬 Engineering Operator Architectural Research & Design References

This document records architectural research notes and comparative design evaluations for Mini-Jules deterministic operators.

## 1. Structural Parsing & Rewriting Backends

### Tree-sitter
- **Repository**: [tree-sitter/tree-sitter](https://github.com/tree-sitter/tree-sitter)
- **Role**: Concrete Syntax Tree (CST) generator supporting multi-language grammar bindings.
- **Evaluation for Mini-Jules**:
  - Mini-Jules Phase D utilizes standard Python `ast` and Python `tokenize` modules for Python symbol renaming without external C dependencies.
  - Tree-sitter is evaluated as the candidate backend for future multi-language structural operators (TypeScript, Go, Rust, Java).

### ast-grep
- **Repository**: [ast-grep/ast-grep](https://github.com/ast-grep/ast-grep)
- **Role**: AST-based code search and structural rewriting CLI tool powered by Tree-sitter.
- **Evaluation for Mini-Jules**:
  - Evaluated as an optional external operator backend for complex structural codemods across multi-file JS/TS repositories.

### OpenRewrite
- **Repository**: [openrewrite/rewrite](https://github.com/openrewrite/rewrite)
- **Role**: Automated refactoring ecosystem for Java/Spring and multi-framework migrations.
- **Evaluation for Mini-Jules**:
  - Mini-Jules adapts OpenRewrite's recipe/precondition design pattern (decoupling inspection, precondition validation, proposal creation, and application).

## 2. Agent Edit Models & Runtime Isolation

### Aider Edit Model
- **Repository**: [Aider-AI/aider](https://github.com/Aider-AI/aider)
- **Role**: Targeted edit blocks and unified diff proposals.
- **Evaluation for Mini-Jules**:
  - Mini-Jules Phase D adopts Aider's principle of generating explicit unified diffs and SHA-256 original content hashes rather than rewriting entire files blindly.

### Continue Plan/Agent Separation
- **Repository**: [continuedev/continue](https://github.com/continuedev/continue)
- **Role**: Explicit separation between planning and execution steps.
- **Evaluation for Mini-Jules**:
  - Mini-Jules enforces mandatory decoupling: `inspect()` -> `plan()` -> `propose()` -> `verify()` -> `apply(approved=True)`.

### OpenHands Runtime & Security Architecture
- **Repository**: [OpenHands/OpenHands](https://github.com/OpenHands/OpenHands)
- **Role**: Containerized runtime sandbox preventing arbitrary host system execution.
- **Evaluation for Mini-Jules**:
  - Validates Phase D's strict separation: static operators generate non-mutating dry-run proposals; execution/sandboxing occurs in a controlled runtime environment.
