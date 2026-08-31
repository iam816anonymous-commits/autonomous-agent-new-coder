# 🛡️ Controlled Runtime Threat Model (Phase E.1)

## Assets & Trust Boundaries
- **Assets**: Workspace source code, developer environment secrets, execution audit trail logs.
- **Trust Boundary**: Unauthenticated natural language requests and untrusted repository code are outside the trust boundary. Predefined command registry and execution policies enforce the runtime boundary.

## Threat Analysis & Mitigations Matrix

| Threat Actor / Vector | Threat Description | Mitigation Strategy | Residual Risk | Verified by Test? |
| :--- | :--- | :--- | :--- | :---: |
| **Command Injection** | Passing shell metacharacters (`;&|`$><`) or shell wrappers (`bash -c`) | Executables checked against blocked list; `shell=False` enforced; argument patterns checked. | None for shell injection. | Yes (`test_shell_injection_argument_rejection`) |
| **Path Traversal / Escape** | Working dir or artifact path escaping workspace (`../../etc`) | Canonical `os.path.commonpath` realpath boundary validation. | None. | Yes (`test_working_directory_boundary`) |
| **Symlink Escape** | Workspace symlink pointing outside repository root | Realpath resolution checks canonical target against repository root. | None. | Yes (`test_symlink_escape_prevention`) |
| **Secret Leakage** | Subprocess logging or inheriting parent process API keys/passwords | Strict environment variable whitelist + regex secret redaction layer. | Low (if script prints un-patterned secret). | Yes (`test_secret_environment_scrubbing`) |
| **Resource Exhaustion** | Infinite loop or memory/output flood in test commands | Process timeout termination + stdout/stderr byte limits. | Low (OS process memory limits require Cgroup/Docker). | Yes (`test_timeout_termination`) |
| **High-Risk Code Run** | Executing arbitrary code in project test suites | Risk categorization (`HIGH`); mandates explicit `execution_approved=True`. | Low. | Yes (`test_high_risk_execution_approval_boundary`) |
| **Workspace Race** | Workspace modified during verification run | Pre/post snapshot hashing (`compute_workspace_snapshot_hash`); flags `WORKSPACE_CHANGED`. | None. | Yes (`test_workspace_change_detection`) |
| **Crash Recovery** | Process terminates midway through verification | Task state machine recovers task to `RECOVERY_REQUIRED`; never marks `PASSED`. | None. | Yes (`test_crash_recovery`) |
