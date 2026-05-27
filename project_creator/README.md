# 🐍 Mini Jules Backend

The engine behind Mini Jules, providing elite orchestration and secure tool execution.

## 🧱 Architecture

### Agents
- **Planner**: Architects multi-module blueprints.
- **Coder**: Generates senior-level, security-aware code.
- **Critique**: Senior logic and security auditor.
- **Repair**: Proposes non-destructive structured JSON patches.

### Core
- **Orchestrator**: Enforces the Sandbox Dry-run and SDLC lifecycle.
- **Tool Executor**: Hardened sandbox with audit logging and shlex parsing.
- **Storage**: Secure file operations using `os.path.realpath` to block traversal.

## 🛡️ Security Features
- **Audit Log**: `agent_audit.log` tracks all subprocess executions.
- **Dry-run**: Generated code is validated in `/tmp` before entering workspace.
- **Constitutional Blocking**: Deny-list for patterns like `sudo`, `chmod`, `.env`.
