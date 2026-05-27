# Changelog

All notable changes to the Mini Jules project will be documented in this file.

## [1.0.0] - 2025-05-22

### Added
- **Autonomous Multi-File Generation**: Complete project architecting and assembly from a single prompt.
- **SDLC Orchestration**: Strict lifecycle enforcing Plan → Generate → Critique → Repair → Approve → Apply.
- **VS Code Extension**: Native sidebar UI with multi-tab support and CodeLens inline actions.
- **Production Manifest**: `project.yaml` source of truth for full project state tracking.
- **Sandbox Constitution**: Secure tool execution with explicit rejection of high-risk operations.
- **Multi-Provider Routing**: Resilient routing with support for Gemini 2.5 Flash, Groq, and OpenRouter.
- **Iterative Self-Repair**: Automated repair loop leveraging LLM critique and tool-based linting.
- **Validation Matrix**: Comprehensive benchmark corpus for various app types (FastAPI, RAG, etc.).

### Fixed
- Fixed JSON extraction resilience for non-deterministic model responses.
- Fixed path traversal vulnerabilities using absolute path resolution.
- Fixed session resumption consistency issues.

### Changed
- Refactored core logic into a unified `Orchestrator` for CLI/Extension parity.
- Hardened agent prompts to elite senior engineering standards.
