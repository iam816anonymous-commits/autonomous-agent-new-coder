# ⚠️ Mini Jules: Limitations & Known Failure Modes (v15)

## Known Failure Modes
1.  **Hallucinated Imports:** Occasionally attempts to import submodules that don't exist in the target environment or library version.
2.  **Package Version Drift:** May use outdated library syntax (e.g., assuming Pydantic v1 when v2 is installed) unless version pins are provided.
3.  **Over-Engineering:** Tendency to apply complex Multi-Agent or RAG patterns to simple CLI tasks if those patterns are fresh in its memory.
4.  **Circular Dependencies:** The topological sorter may struggle if the prompt design encourages tight coupling between core models and API layers.
5.  **Weak Semantic Repair:** While excellent at fixing syntax and imports, deep logical or algorithmic bugs often lead to repair loops that require human intervention.

## Architectural Weaknesses
*   **Scale Limits:** Performance degrades on monolithic repositories containing >1000 files during full workspace scans.
*   **Language Bias:** Heavily optimized for Python; pattern extraction for Go/Rust/Java is currently limited to structural heuristics.
*   **Context Window Drift:** In extremely large generation tasks, the agent may lose alignment with the `Strategy Document` if not explicitly reminded in stage prompts.

## Unsupported Scenarios
*   **GUI/Mobile Testing:** No support for automated UI interaction testing (Selenium/Appium/Cypress).
*   **Root-Level Operations:** The Sandbox Constitution strictly forbids commands requiring `sudo` or modification of system files.
*   **Legacy Refactors:** Designed for surgical repair and greenfield generation; not a general-purpose "Rewrite my legacy app" tool.

---
*Documented as of Hardened v15 release.*
