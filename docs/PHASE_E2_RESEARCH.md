# Phase E.2 Security Research & Architecture Principles

## 1. Executive Summary
Phase E.2 addresses the fundamental security requirement of autonomous engineering engines: **treating repository code as untrusted input**. While static analysis (e.g., AST parsing, regex scanning, file hashing) inspects code without executing it, running tests or tools like `pytest`, `python`, `node`, or build scripts triggers code execution within repository modules, test fixtures, and dependencies.

Command allowlisting (e.g., allowing `pytest`) is necessary but insufficient on its own because `pytest` imports and executes arbitrary Python code from the repository. Therefore, Phase E.2 implements capability isolation, transactional workspace management, explicit execution trust levels, and sandbox backends.

---

## 2. Primary Research & Theoretical Guidance

### 2.1 OWASP Command & Code Injection Guidance
* **Principle**: Shell string concatenation or execution via shell interpreters (`shell=True`, `/bin/sh -c`) invites command injection via metacharacters (`;&|$><`\`\n`).
* **Mitigation**: Mini-Jules enforces structured argument arrays (`execve`-style) with `shell=False`.
* **Repository Untrusted Code Hazard**: Command injection is not limited to standard input; running tools like `pytest` executes arbitrary code contained in untrusted `conftest.py` or test files. Thus, process-level isolation and workspace sandboxing are required.

### 2.2 Capability-Based Security (Saltzer & Schroeder, 1975)
* **Principle of Least Privilege**: Processes must operate with the minimum set of privileges required to perform their task.
* **Deny-by-Default Architecture**: Access is denied unless explicitly granted via typed capabilities (`ExecutionCapability.STATIC_ANALYSIS`, `RUN_TESTS`, `READ_WORKSPACE`, `WRITE_WORKSPACE`, `NETWORK`).
* **Capability Escalation Prevention**: Child execution environments cannot claim or inherit capabilities that were not explicitly granted by the parent security policy.

### 2.3 Sandboxing Principles & OpenHands Architecture Insights
* **Static vs Dynamic Separation**: The engine explicitly separates non-executing static analysis (`STATIC_ONLY`) from dynamic code execution (`RESTRICTED_LOCAL` or `ISOLATED`).
* **Transactional Workspace Isolation**: Modifications and test runs occur within copy-on-write or transactional execution workspaces rather than mutating the original workspace directly.
* **Honest Limitation Reporting**: The system explicitly reports OS-level enforcement limits (e.g., local process execution vs container network isolation) rather than claiming false security guarantees.

---

## 3. Threat Model & Risk Vectors

| Risk Vector | Threat Description | Phase E.2 Mitigation Strategy |
| :--- | :--- | :--- |
| **Path Traversal Escape** | Malicious file paths (e.g., `../../etc/passwd`) targeting host filesystem. | Realpath boundary validation (`os.path.commonpath`) rejecting paths outside workspace. |
| **Symlink Escape** | Workspace contains symlinks pointing to sensitive host directories. | Symlink resolution checks rejecting escape symlinks during copy and traversal. |
| **Secret Inheritance** | Child execution inherits parent process API keys/secrets from `os.environ`. | Environment whitelist sanitization and redaction of parent process environment variables. |
| **Implicit Mutation** | Test failure leaves workspace in corrupted or partially modified state. | Transactional workspace with `DISCARD_ALWAYS` or `COMMIT_ON_SUCCESS` policies. |
| **Capability Escalation** | Low-trust task requests test execution or network access. | Strict `CapabilitySet` checking with fail-closed validation. |
| **False Isolation Report** | Claiming OS network isolation when running in local process. | Explicit `enforcement_limitations` metadata in sandbox execution results. |

---

## 4. Implementation Design Principles

1. **Local-First & Deterministic**: No cloud or LLM dependencies required for security decisions.
2. **Fail-Closed**: Unknown capabilities, expired approvals, or missing backends fail closed.
3. **Optional Container Isolation**: Docker integration is fully supported when available, but degrades gracefully without crashing when Docker is unavailable.
4. **Structured Snapshot Diffing**: Streaming file hashes provide exact file-level change tracking (`ADDED`, `MODIFIED`, `DELETED`, `UNCHANGED`).
