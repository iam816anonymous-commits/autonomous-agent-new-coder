# 🤖 Agent Instructions for Mini Jules

As an AI agent working on this repo, you MUST strictly adhere to the following constitution.

## 🏗️ Immutable Architecture
1. **Orchestrator Centrality**: All SDLC logic (Plan → Generate → Dry-run → Critique → Apply) MUST reside in `project_creator/core/orchestrator.py`.
2. **Atomic Writing**: Use `Storage.write_file` for all file operations. Never use raw `open()` for project files.
3. **Resilient Parsing**: Use `project_creator.core.utils.extract_json` for all LLM response parsing.

## 🛡️ Security Constitution
1. **Sandbox Enforcement**: Tool execution MUST happen via `ToolExecutor`. NEVER use `shell=True`.
2. **Audit Accountability**: Ensure all whitelisted commands are being logged.
3. **Prompt Hardening**: Maintain senior engineering standards in all agent prompts (type hints, security focus).

## 🧪 Compliance
- **Validation**: Run `validate_jules.py` to benchmark any changes to the generation loop.
- **Hygiene**: NEVER commit `__pycache__` or `.agent_session.json` files.

---
*Governance is not optional.*
