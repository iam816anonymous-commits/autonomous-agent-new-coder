# 📜 Refactoring Recipe Architecture Model

## Overview
Inspired by OpenRewrite's recipe architecture, Mini-Jules operators adopt a composable, recipe-based transformation pipeline.

## Recipe Lifecycle

```text
Recipe
 ├── Metadata (Name, TaskType, Required Capabilities)
 ├── Preconditions (Satisfied check, SHA-256 checks, ambiguity checks)
 ├── Transformations (Deterministic token/AST rewriting, dry-run diffs)
 ├── Verification (Syntax parsing, structural integrity checks)
 └── Rollback (Targeted transaction state restoration)
```

## Mini-Jules Operator Mapping
- **`inspect()`**: Evaluates preconditions and repository symbol state.
- **`plan()`**: Formulates machine-readable execution steps.
- **`propose()`**: Performs dry-run transformations and yields unified diffs without modifying files.
- **`verify_proposal()`**: Runs post-transformation AST syntax validation.
- **`apply()`**: Validates SHA-256 hashes, applies file mutations upon approval, and triggers automatic rollback on verification failure.
