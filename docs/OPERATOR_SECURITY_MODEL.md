# 🔒 Engineering Operator Security & Capability Policy Model

## Overview
Mini-Jules enforces capability-based permission boundaries for all engineering operators. Operators declare fine-grained capability metadata required to inspect, plan, propose, and apply changes.

## Capability Hierarchy

```text
Capability
    ├── repository.scan          (Read-only static scanning)
    ├── repository.symbols       (Read-only symbol index querying)
    ├── repository.dependencies  (Read-only dependency graph analysis)
    ├── filesystem.read          (Read-only file reading)
    ├── filesystem.write         (Workspace file writing)
    ├── filesystem.rename        (Workspace file renaming/moving)
    ├── patch.generate           (Unified diff generation)
    └── verification             (AST/syntax verification checks)
```

## Security Pipeline

```text
Capability Declaration
          │
          ▼
   Operator Metadata
          │
          ▼
Risk Level Assessment (LOW, MEDIUM, HIGH, CRITICAL)
          │
          ▼
Approval Requirement (approved=True mandatory for filesystem.write)
          │
          ▼
SHA-256 Stale Check (Rejects modified workspace state)
          │
          ▼
Targeted Transaction Rollback (Restores only operator-owned files on error)
```

## Safety Boundaries
- **No Unsanitized Shell Execution**: Operators do not execute arbitrary shell strings or external scripts.
- **Path Traversal Protection**: All file read/write operations verify realpath workspace boundaries (`_is_safe_path`).
- **Human Approval Boundary**: Mutation operations (`apply`) reject execution unless `approved=True` is explicitly passed.
