# 🔒 Controlled Verification Runtime Threat Model & Security Specification

## Overview
Phase E implements a capability-controlled verification runtime (`engine.runtime`). The runtime executes predefined verification commands (syntax checks, linters, tests) **without shell interpreters or arbitrary command execution**.

## Threat Model & Mitigations

### 1. Arbitrary Command Injection
- **Threat**: User or untrusted repository attempts shell injection via `bash -c "rm -rf /"` or command chaining (`pytest; rm -rf /`).
- **Mitigation**: Executables are checked against `BLOCKED_EXECUTABLES` (`bash`, `sh`, `zsh`, `cmd`, `powershell`). Commands are constructed using argument arrays (`cmd_args = [executable] + base_args + extra_args`) strictly executed with `shell=False`. Arguments containing shell special characters (`;&|`$><`) are rejected during registration.

### 2. Working Directory & Symlink Escapes
- **Threat**: Subprocess attempts working directory traversal (`cwd="../../etc"`) or symlink escape outside repository workspace.
- **Mitigation**: `RuntimePolicy.validate_working_directory()` enforces realpath boundary validation. Paths escaping the repository root raise `WorkingDirectoryEscapeError`.

### 3. Environment Secret Leakage
- **Threat**: Subprocess logs or test outputs leak parent environment secrets (AWS keys, API tokens).
- **Mitigation**: `RuntimePolicy.sanitize_environment()` uninherits parent secrets and filters environment variables against a strict whitelist (`PATH`, `PYTHONPATH`, `HOME`, `USER`, `TMPDIR`, `LANG`).

### 4. Timeout & Output Exhaustion
- **Threat**: Long-running or infinite loop process exhausts CPU/memory resources or generates gigabytes of logs.
- **Mitigation**: Subprocess execution enforces explicit timeouts (`timeout_seconds`), terminating processes upon expiration (`TIMED_OUT`). Output streams are capped at `max_stdout_bytes` and `max_stderr_bytes` (truncating logs if exceeded).

### 5. High-Risk Code Execution
- **Threat**: Running repository tests executes arbitrary code written in project files.
- **Mitigation**: Verification steps are categorized by risk level (`LOW` for syntax checks, `HIGH` for test suites). High-risk execution requires explicit human execution approval (`execution_approved=True`), raising `ExecutionApprovalRequiredError` if missing.

## Known Security Limitations
- `LocalRestrictedEnvironment` runs on the host process system. It does not enforce OS kernel-level network namespace blocking or cgroup memory limits. Untrusted code execution in test suites remains a host risk until containerized `DockerEnvironment` is deployed in future phases.
