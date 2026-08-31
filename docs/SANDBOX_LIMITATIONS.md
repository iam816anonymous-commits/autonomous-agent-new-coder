# Sandbox Security Limitations & Disclosure

## 1. Honest Disclosure Policy
Mini-Jules adheres to an honest security disclosure policy: **we never claim security guarantees that cannot be enforced by the underlying OS environment**.

---

## 2. Specific Backend Limitations

### 2.1 Static-Only Backend (`STATIC_ONLY`)
* **Enforced**: 100% guarantee against process execution. Command invocation attempts fail closed.
* **Limitation**: AST parsing or regex analysis of untrusted files can theoretically cause high CPU/memory consumption if malicious, huge, or deeply nested files are parsed.

### 2.2 Restricted Local Backend (`RESTRICTED_LOCAL`)
* **Enforced**:
  - `shell=False` execution prevents shell metacharacter injection (`;&|$><`).
  - Predefined command allowlisting and strict regex argument schema validation.
  - Workspace realpath boundary validation blocking path traversal.
  - Environment variable sanitization preventing secret inheritance.
* **Limitations**:
  - **No Kernel Network Isolation**: Local process execution relies on OS user privileges. Network socket blocking is best-effort and cannot be guaranteed without kernel network namespace isolation.
  - **Host Permission Reliance**: Code executed via `pytest` runs under the permissions of the host user running Mini-Jules.
  - **Resource Limits**: Memory and CPU quota limits are constrained to process timeouts and stdout/stderr byte truncation limits.

### 2.3 Container Sandbox Backend (`ISOLATED`)
* **Enforced**:
  - Kernel-level network isolation (`--network none`).
  - Isolated container filesystem with workspace mounted read-write.
* **Limitations**:
  - **Docker Requirement**: Requires Docker daemon running on host. If Docker is missing or unresponsive, backend fails closed with `BackendUnavailableError`.
