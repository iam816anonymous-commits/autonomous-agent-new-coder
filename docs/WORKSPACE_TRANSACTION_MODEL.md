# Workspace Transaction Model

## 1. Overview
The `WorkspaceTransaction` engine ensures that test execution, verification commands, and dry-run proposals never corrupt or pollute the developer's original repository workspace.

---

## 2. Transaction Policies

1. **`READ_ONLY`**:
   - Operations execute directly against the original workspace root.
   - If any file is added, modified, or deleted during execution, a `TransactionError` is raised immediately.

2. **`DISCARD_ALWAYS`**:
   - Creates a temporary isolated copy of the workspace using `WorkspaceManager.create_isolated_copy()`.
   - All tool executions occur inside the isolated copy.
   - Upon completion or failure, the isolated workspace is destroyed. The original workspace remains pristine.

3. **`COMMIT_ON_SUCCESS`**:
   - Executes inside an isolated copy.
   - If verification passes **AND** explicit commit authorization is provided (`ExecutionCapability.WRITE_WORKSPACE`), diff changes are applied back to the original workspace after realpath boundary validation.

---

## 3. Path Traversal & Symlink Escape Guards

* **Realpath Commonpath Verification**: Every path read or write validates that `os.path.commonpath([workspace_root, target_path]) == workspace_root`.
* **Symlink Resolution Checks**: `WorkspaceManager.validate_symlink_target()` resolves all symlink targets and rejects any links pointing outside the workspace boundary.
