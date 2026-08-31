# Phase E.2 Final Report: Transactional Workspace Sandbox, Capability Isolation & Safe Verification

## 1. Executive Summary
Phase E.2 expands **Mini-Jules** with a robust, local-first, deterministic sandboxing and capability isolation engine under `engine/runtime/sandbox/`. The subsystem treats repository code as untrusted input, explicitly distinguishing static analysis from dynamic code execution.

All operations execute without LLM or network dependencies, maintaining 100% offline determinism and passing the full regression test suite (81/81 passed).

---

## 2. Architecture & Components Created

```text
engine/runtime/sandbox/
├── __init__.py
├── models.py            # SandboxMode, ExecutionCapability, ExecutionTrustLevel, SandboxSpec, SandboxResult, ExecutionApproval
├── errors.py            # CapabilityViolationError, WorkspaceEscapeError, BackendUnavailableError, ApprovalExpiredError
├── capabilities.py      # CapabilitySet with deny-by-default and escalation prevention
├── snapshot.py          # Streaming workspace snapshotter & deterministic diff generator (WorkspaceDiff, WorkspaceChange)
├── workspace.py         # WorkspaceManager for isolated workspace copy creation & realpath/symlink boundary checks
├── transaction.py       # WorkspaceTransaction supporting DISCARD_ALWAYS, COMMIT_ON_SUCCESS, READ_ONLY
├── backend.py           # Abstract SandboxBackend interface
├── static_backend.py    # StaticOnlyBackend (fails closed on process execution attempts)
├── local_backend.py     # RestrictedLocalBackend (shell=False, secret blocking, path boundary check, limit disclosure)
├── container_backend.py # ContainerSandboxBackend (Optional Docker isolated container backend with safe fallback)
└── manager.py           # SandboxManager orchestrator & audit evidence logger
```

---

## 3. Key Technical Guarantees

1. **Deny-by-Default Capability Security**:
   - Capabilities (`STATIC_ANALYSIS`, `READ_WORKSPACE`, `WRITE_WORKSPACE`, `EXECUTE_COMMAND`, `RUN_TESTS`) must be explicitly granted.
   - Capability escalation by child execution environments is strictly rejected.

2. **Static vs Dynamic Isolation**:
   - Static analysis (`STATIC_ONLY`) guarantees zero process execution. Dynamic command or test execution attempts fail closed.

3. **Transactional Workspace Safety**:
   - Verification execution occurs inside an isolated workspace copy (`DISCARD_ALWAYS` or `READ_ONLY`).
   - Original workspace is preserved against test side effects or failures.
   - Commit back to original workspace (`COMMIT_ON_SUCCESS`) requires explicit authorization and target realpath boundary verification.

4. **Path Traversal & Symlink Escape Guards**:
   - Paths are validated using `os.path.commonpath([workspace_root, target])`.
   - Symlinks target verification (`WorkspaceManager.validate_symlink_target`) blocks escapes to host directories outside the workspace.

5. **Optional Docker Support & Graceful Fallback**:
   - `ContainerSandboxBackend` supports Docker isolated execution when available (`--network none`).
   - If Docker is missing or misconfigured, the backend raises `BackendUnavailableError` without crashing.

---

## 4. Test Verification Summary

* **Total Tests Executed**: 81
* **Pass Rate**: 100% (81/81 passed)
* **Test Suites Covered**:
  - `tests/test_repository_knowledge_graph.py` (10 tests)
  - `tests/test_task_state_machine.py` (11 tests)
  - `tests/test_task_classifier.py` (20 tests)
  - `tests/test_engineering_operators.py` (11 tests)
  - `tests/test_runtime_commands.py` (6 tests)
  - `tests/test_runtime_policy.py` (5 tests)
  - `tests/test_runtime_executor.py` (3 tests)
  - `tests/test_verification_runtime.py` (4 tests)
  - `tests/test_sandbox_models.py` (6 tests)
  - `tests/test_sandbox_backends.py` (5 tests)

---

## 5. Limitation Disclosures & Future Recommendations

* **Local Restriction Limitation**: As documented in `docs/SANDBOX_LIMITATIONS.md`, local process execution (`RESTRICTED_LOCAL`) enforces argument array safety, secret blocking, and working dir realpath boundaries, but cannot enforce kernel-level network socket blocking without containerization.
* **Phase E.3 Recommendation**: Expand verification capabilities to support automated failure classification and deterministic repair loops operating inside transactional sandboxes.
