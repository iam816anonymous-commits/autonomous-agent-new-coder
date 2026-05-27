# 🤖 Agent Instructions for Mini Jules

As an AI agent working on this repository, you must adhere to the following rules and standards.

## 🏗️ Architectural Integrity
- **Orchestrator-First**: All SDLC logic must reside in `project_creator/core/orchestrator.py`. Do not duplicate generation logic in `main.py` or `server.py`.
- **Manifest as Source of Truth**: Any state change (approvals, file additions, status updates) must be reflected in `project.yaml` via the `ProjectManifest` class.
- **Provider Priority**: Maintain the priority: Gemini 2.5 Flash -> Groq -> OpenRouter -> Browser.

## 🛡️ Sandbox Constitution
- NEVER use `shell=True` in subprocess calls.
- Always use `shlex.split` for command parsing.
- Block all system-mutating commands (chmod, chown, sudo) and credential access (.env, passwd).
- All file operations must use `Storage._safe_join` to prevent path traversal.

## 📝 Coding Standards
- **Python**: Use type hints, docstrings, and follow PEP 8.
- **TypeScript**: Use strict typing and avoid `any` where possible.
- **LLM Prompts**: Ensure prompts for `CoderAgent` and `RepairAgent` enforce high-quality, secure code generation (senior engineering standards).

## 🧪 Verification
- Always run the `validate_jules.py` script after significant changes to the generation loop.
- Verify that the FastAPI backend loads correctly using `python -m py_compile project_creator/server.py`.

---
*Mini Jules is a governed ecosystem. Respect the boundaries.*
