# ⚠️ Mini Jules: Limitations & Weaknesses

## Known Weaknesses
1.  **Circular Dependencies:** The topological sorter may fail or produce suboptimal orders if the prompt design encourages tight coupling or circular imports.
2.  **Context Window Drifts:** In extremely large projects (100+ files), the agent may lose track of earlier architectural decisions unless they are explicitly in the `Strategy Document`.
3.  **Non-Python Performance:** While it can "read" multiple languages, its ability to "fix" JS/TS or Rust code in the sandbox is significantly lower than Python.
4.  **Complex Logic Repairs:** The `RepairAgent` is excellent at syntax and configuration, but may get stuck in loops trying to fix deep algorithmic bugs.

## Failure Modes
*   **Model Hallucination:** If the memory retriever returns irrelevant patterns, the agent may attempt to inject incorrect idioms.
*   **Sandbox Isolation Escapes:** While whitelisted, a sufficiently complex Python script could still attempt dangerous operations if not monitored.
*   **Database Corruption:** Concurrent access to the SQLite memory during heavy learning cycles can occasionally cause locking issues (mitigated by `DatabaseManager`).

## Unsupported Scenarios
*   **GUI Applications:** No current support for building or testing desktop/native mobile UIs.
*   **Legacy Refactors:** Mini Jules is optimized for greenfield generation or surgical repair, not for rewriting massive legacy codebases.
*   **High-Privilege Ops:** The sandbox constitution forbids operations requiring `root` or `admin` access.

## Planned Improvements
*   [ ] Memory decay mechanisms for outdated patterns.
*   [ ] Enhanced support for TypeScript/Node.js sandboxing.
*   [ ] Multi-agent "War Gaming" for architectural stress testing.
