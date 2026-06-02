# 🤖 Mini Jules: Production-Hardened Autonomous Engineering Agent

Mini Jules is a high-performance autonomous engineering agent designed to architect, generate, and repair full-stack projects using elite AI models (Gemini 2.5 Flash, Groq, OpenRouter). It features a security-first SDLC loop and integrates directly into VS Code.

## 🚀 Key Features

- **Engineering Brain**: Strategic reasoning, architectural memory, and cross-repo pattern extraction.
- **Autonomous Multi-File Generation**: From single prompt to logically grouped modules using topological dependency sorting.
- **Decomposed SDLC Loop**: High-performance lifecycle orchestrated by specialized coordinators (Generation, Execution, Repair).
- **Security Constitution**: Hardened prompts and physical content validation that proactively block vulnerabilities.
- **Sandbox Dry-run**: Automatic linting and validation of generated code in isolated temporary directories.
- **Production Audit Logging**: Every command executed by the agent is recorded in `agent_audit.log`.
- **VS Code Native**: Sidebar GUI, CodeLens inline actions, and native diff-based patch reviews.
- **Multi-Provider Routing**: Resilient fallback chain with exponential backoff retries.

## 📦 Project Structure

- `project_creator/`: Python backend (Agents, Orchestrator, FastAPI bridge).
- `mini-jules-vscode/`: TypeScript VS Code extension (GUI, Workspace integration).

## 🛠️ Setup

### Backend
```bash
pip install -r requirements.txt
python -m project_creator.server
```

### VS Code Extension
```bash
cd mini-jules-vscode
npm install
npm run compile
```

## 🛡️ Sandbox Constitution
Mini Jules is restricted to a whitelisted set of commands (`pytest`, `ruff`, `black`, `python3`). It is strictly blocked from shell escalation, system mutations, or credential edits.

---
*Mini Jules: Building secure software autonomously.*
