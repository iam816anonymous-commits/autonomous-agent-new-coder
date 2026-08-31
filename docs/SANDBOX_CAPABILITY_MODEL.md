# Sandbox Capability Security Model

## 1. Core Principles
* **Deny-by-Default**: Every capability must be explicitly granted in a `CapabilitySet`.
* **Escalation Prevention**: Child execution contexts cannot request or claim capabilities not present in the parent policy.
* **Fail-Closed**: Any ungranted capability check raises a `CapabilityViolationError`.

---

## 2. Capabilities Grid

| Capability | Description | Granted in STATIC_ONLY | Granted in RESTRICTED_LOCAL | Granted in ISOLATED |
| :--- | :--- | :---: | :---: | :---: |
| `STATIC_ANALYSIS` | AST parsing, scanning, hashing | Yes | Yes | Yes |
| `READ_WORKSPACE` | Reading repository files | Yes | Yes | Yes |
| `WRITE_WORKSPACE` | Modifying repository files | No | Optional | Optional |
| `EXECUTE_COMMAND` | Spawning verification tools | No | Yes | Yes |
| `RUN_TESTS` | Running unit/full test suites | No | Yes | Yes |
| `NETWORK` | Sockets / internet connections | No | No (Denied) | No (Denied) |
| `INSTALL_DEPENDENCY`| Modifying lockfiles / pip | No | No (Denied) | No (Denied) |
