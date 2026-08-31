# Phase E.2 Sandbox Architecture

## 1. Overview
The **Transactional Workspace Sandbox & Capability Isolation Subsystem** provides deterministic, local-first execution sandboxing for Mini-Jules. It separates non-executing static analysis from potentially dynamic repository code execution while enforcing fine-grained capability checks, path safety, and transactional workspace rollbacks.

---

## 2. Directory Structure & Component Hierarchy

```text
engine/runtime/sandbox/
├── __init__.py
├── models.py            # Typed enums and dataclasses (SandboxMode, ExecutionCapability, etc.)
├── errors.py            # Typed exception hierarchy (CapabilityViolationError, WorkspaceEscapeError, etc.)
├── capabilities.py      # CapabilitySet with deny-by-default rules and escalation prevention
├── snapshot.py          # Streaming workspace snapshotter & deterministic diff generator
├── workspace.py         # Isolated workspace manager & symlink escape validator
├── transaction.py       # WorkspaceTransaction supporting DISCARD_ALWAYS, COMMIT_ON_SUCCESS, READ_ONLY
├── backend.py           # Abstract SandboxBackend interface
├── static_backend.py    # StaticOnlyBackend (zero code execution guarantee)
├── local_backend.py     # RestrictedLocalBackend (OS-level process execution with boundary checks)
├── container_backend.py # ContainerSandboxBackend (Optional Docker isolated container backend)
└── manager.py           # SandboxManager orchestrator & audit evidence logger
```

---

## 3. Sandbox Execution Modes

1. **`STATIC_ONLY`**:
   - Strictly reserved for AST parsing, static analysis, regex symbol indexing, and file hashing.
   - Dynamic process execution attempts are rejected at runtime (`fail-closed`).

2. **`RESTRICTED_LOCAL`**:
   - Executes allowed verification commands locally via structured argument arrays (`shell=False`).
   - Sanitizes parent environment variables to prevent secret inheritance.
   - Enforces realpath workspace boundary validation (`os.path.commonpath`).
   - Discloses local isolation limitations in execution metadata.

3. **`ISOLATED`**:
   - Executes commands inside a containerized environment (e.g., Docker).
   - Enforces network disabled (`--network none`), non-root execution, and read-write workspace mounting.
   - Degrades gracefully if Docker is unavailable without crashing the system.

---

## 4. Operational Flow Diagram

```text
  Verification Profile / Task Request
                  │
                  ▼
        Validate Approval & Fingerprint
                  │
                  ▼
        Initialize Workspace Transaction
      (Capture Snapshot_Before & Copy Workspace)
                  │
                  ▼
         Select Sandbox Backend
     (StaticOnly / Local / Container)
                  │
                  ▼
         Execute Command (shell=False)
                  │
                  ▼
         End Workspace Transaction
      (Capture Snapshot_After & Diff)
                  │
      ┌───────────┴───────────┐
      ▼                       ▼
 Success + Auth            Failure or Discard
  (Commit to Workspace)    (Discard Sandbox Copy)
                  │
                  ▼
       Persist Audit Artifacts
```
