# ⚙️ Deterministic Engineering Operator Framework (Phase D)

## Overview
Phase D introduces the **Deterministic Engineering Operator Framework** (`engine.operators`). Operators transform task classifications into safe, inspectable, dry-run proposals containing unified diffs and SHA-256 integrity hashes—**100% offline without LLM dependencies**.

## Operator Lifecycle

```text
Classified Request
        │
        ▼
   Registry Lookup
        │
        ▼
  INSPECT (inspect) ──► Analyze preconditions and symbol index
        │
        ▼
    PLAN (plan)    ──► Machine-readable step sequence
        │
        ▼
PROPOSE (propose)  ──► Dry-run diff & SHA-256 generation (Modifies NOTHING)
        │
        ▼
 VERIFY PROPOSAL   ──► Validate AST syntax & boundary security
        │
        ▼
APPROVAL BOUNDARY ──► approved=False raises ApprovalRequiredError
        │
        ▼
   APPLY (apply)   ──► Verify SHA-256 stale check -> Mutate workspace -> Post-verify
        │
  (on error/failure)
        ▼
    ROLLBACK       ──► Targeted rollback of operator-owned file changes only
```

## Core Safety Properties

1. **Mandatory Dry-Run (`propose`)**:
   Calling `propose()` calculates unified diffs, expected SHA-256 hashes, and preconditions, but modifies zero files on disk.

2. **SHA-256 Stale Proposal Rejection**:
   Before modifying workspace files in `apply()`, the operator verifies that the current SHA-256 content hash matches the proposal's `old_sha256`. If the workspace was modified after proposal creation, a `StaleProposalError` is raised.

3. **Explicit Approval Boundary**:
   Calling `apply()` with `approved=False` raises `ApprovalRequiredError` and aborts without workspace changes.

4. **Targeted Rollback**:
   If post-verification fails during `apply()`, the operator restores only the files modified or created during that operator transaction ID.

5. **Token-Based Symbol Renaming**:
   `SymbolRenameOperator` uses Python AST and tokenizer tokens to rename exact identifiers without false-positive string/substring collisions.

## Builtin Operators
- **`SymbolRenameOperator`**: Handles `SYMBOL_RENAME` using AST token rewriting.
- **`FileMoveOperator`**: Handles `FILE_MOVE` and `FILE_RENAME` with dependency impact reporting.

## Debug CLI Commands

```bash
# Generate deterministic execution plan (no mutations)
python -m engine.cli plan "Rename calculate_total to calculate_invoice_total" --root /path/to/repo

# Generate dry-run proposal with unified diffs (no mutations)
python -m engine.cli propose "Rename calculate_total to calculate_invoice_total" --root /path/to/repo

# Apply changes with explicit approval flag
python -m engine.cli apply "Rename calculate_total to calculate_invoice_total" --root /path/to/repo --approved
```
