# 🤖 Mini Jules: Autonomous Multi-File Project Generator

Mini Jules is an autonomous engineering agent designed to architect, generate, and repair full-stack projects using a suite of high-performance AI models (Gemini 2.5 Flash, Groq, OpenRouter). It integrates directly into VS Code as a native extension, providing a seamless Developer Experience (DX).

## 🚀 Key Features

- **Autonomous Project Creation**: From a single prompt to a structured multi-file project.
- **SDLC Orchestration**: Strict lifecycle (Plan → Generate → Critique → Repair → Approve → Apply).
- **Multi-Provider Routing**: Primary Gemini 2.5 Flash with resilient fallbacks to Groq, OpenRouter, and ChatGPT Browser.
- **VS Code Native**: Sidebar GUI, CodeLens inline actions, and native diff-based patch reviews.
- **Secure Sandbox**: Strictly whitelisted tool execution and path traversal protection.
- **Project Manifest**: YAML-based source of truth tracking goals, stacks, and files.

## 📦 Project Structure

- `project_creator/`: Python backend containing the agentic engine and FastAPI bridge.
- `mini-jules-vscode/`: TypeScript VS Code extension for the GUI and editor integration.

## 🛠️ Getting Started

### 1. Requirements
- Python 3.10+
- Node.js & npm
- Gemini/Groq/OpenRouter API Keys

### 2. Setup Backend
```bash
pip install -r requirements.txt
python -m project_creator.server
```

### 3. Setup Extension
```bash
cd mini-jules-vscode
npm install
npm run compile
```
Then load the extension in VS Code.

## 🛡️ Governance & Safety
Mini Jules operates under a strict **Sandbox Constitution**. It can format code and run tests but is blocked from credential mutation, shell escalation, or recursive self-modification.

---
*Built for the next generation of autonomous software engineering.*
