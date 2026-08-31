# 🔬 Controlled Verification Runtime Architectural Research & Design References

This document records architectural research notes and comparative design evaluations for Mini-Jules controlled verification runtime.

## 1. External Architecture Evaluations

### OpenHands
- **Role**: Sandboxed container runtime isolating agent actions and preventing arbitrary host execution.
- **Mini-Jules Adaptation**: Phase E adopts OpenHands' principle of separating execution policy, action validation, and risk tiers (`LOW`, `MEDIUM`, `HIGH`). High-risk execution (running project pytest suites) requires explicit `execution_approved=True`.

### SWE-agent
- **Role**: Trajectory recording and reproducible execution environment artifacts.
- **Mini-Jules Adaptation**: Mini-Jules persists structured execution artifacts (`ExecutionResult`, stdout/stderr logs) under `task_artifacts/` using `ArtifactManager`.

### Aider
- **Role**: Non-interactive command execution for test verification post-edit.
- **Mini-Jules Adaptation**: Mini-Jules strictly decouples proposal generation (`propose`) from verification execution (`verify`).

## 2. Local vs. Containerized Isolation Comparison

| Feature | `LocalRestrictedEnvironment` (Phase E) | `DockerEnvironment` (Future Phase) |
| :--- | :--- | :--- |
| **Shell Access** | Strictly `shell=False` | Strictly `shell=False` |
| **Command Injection** | Blocked via argument arrays | Blocked via argument arrays |
| **Environment Secret Filtering** | Whitelist + Secret scrubbing | Complete container isolation |
| **Working Dir Boundary** | Realpath root check (`_is_safe_path`) | Container bind mount isolation |
| **Network Isolation** | Partial / OS dependent | Full (`--network none`) |
| **CPU / Memory Limits** | Output truncation + Process timeout | Kernel cgroups enforcement |

## 3. Current Implementation Status vs. Future Work
- **Implemented**: `LocalRestrictedEnvironment` with `shell=False`, working directory realpath boundary checks, process timeout termination, stdout/stderr byte limits, secret environment scrubbing, and high-risk execution approval boundaries.
- **Future Work**: Containerized `DockerEnvironment` for full OS-level cgroup resource limits and network namespace isolation.
