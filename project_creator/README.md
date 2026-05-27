# 🐍 Mini Jules Backend

This directory contains the core agentic engine for Mini Jules, built with Python and FastAPI.

## 🧱 Architecture

### Agents
- **Planner**: Architects the project blueprint and module structure.
- **Coder**: Generates high-quality, senior-level source code.
- **Critique**: Audits code for defects, security issues, and architectural parity.
- **Repair**: Proposes structured JSON patches to resolve audit issues.

### Core Modules
- **Orchestrator**: Manages the unified SDLC lifecycle across CLI and API.
- **Provider Router**: Handles model priority and resilient fallbacks with exponential backoff.
- **Project Manifest**: Manages `project.yaml` as the central source of truth.
- **Tool Executor**: Safe execution of `pytest`, `ruff`, and `black`.

## 📡 API Endpoints

- `POST /start`: Initializes a project and generates a blueprint.
- `POST /process_file`: Runs the Generate-Critique-Repair loop for a file.
- `POST /approve`: Applies a generated/repaired file to the workspace.
- `GET /manifest`: Returns the current project status.

## 🔑 Environment Variables

- `GEMINI_API_KEY`: Required for primary inference.
- `GROQ_API_KEY`: Optional fallback.
- `OPENROUTER_API_KEY`: Optional fallback.
- `GEMINI_MODEL`: Default is `gemini-2.5-flash`.
