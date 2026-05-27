# 🗺️ Mini Jules: Offline Learning Evolution Roadmap

This roadmap outlines the transition from a production engineering agent to a personalized, self-improving offline engineering brain.

## Phase 1: Activity Collector (Foundation)
- [ ] Implement `event_bus.py` for decoupled event tracking.
- [ ] Create `collector.py` to ingest workspace events (file opens, manual edits).
- [ ] Implement `workspace_monitor.py` for real-time file system awareness.
- [ ] **Goal**: Capture the digital exhaust of development without leaking secrets.

## Phase 2: Coding Memory (Persistence)
- [ ] Setup SQLite schema for sessions, patterns, snippets, and user styles.
- [ ] Implement indexing for imports and architecture structures.
- [ ] **Goal**: Local, private storage of personalized coding history.

## Phase 3: Pattern Learner (Intelligence)
- [ ] Build `pattern_learner.py` to identify repeated imports and naming conventions.
- [ ] Implement preference scoring for different frameworks (FastAPI, Streamlit).
- [ ] **Goal**: Distill raw activity into actionable preferences.

## Phase 4: Retrieval Engine (Context)
- [ ] Create `retriever.py` to inject learned patterns into agent prompts.
- [ ] Link retriever to `CoderAgent` and `PlannerAgent`.
- [ ] **Goal**: Immediate improvement in generation quality based on local history.

## Phase 5: Local Vector Memory (Search)
- [ ] Integrate FAISS for semantic search over code snippets and repairs.
- [ ] Implement `vector_store.py` for embedding management.
- [ ] **Goal**: High-fidelity retrieval of relevant past solutions.

## Phase 6: Offline Model Support (Autonomy)
- [ ] Add `ollama_provider.py` to support local models (Qwen2.5-Coder, DeepSeek).
- [ ] **Goal**: 100% private, cloud-free engineering workflow.

## Phase 7: Safe Learning Constitution (Governance)
- [ ] Implement strict filtering to ensure no secrets or .env files are ever stored.
- [ ] **Goal**: Military-grade privacy and data security.

## Phase 8: VS Code Memory UI (DX)
- [ ] Extend Sidebar with "Memory" and "Patterns" tabs.
- [ ] Allow users to view, edit, or forget learned behaviors.
- [ ] **Goal**: Transparency and control over the agent's brain.

## Phase 9: Future Training Prep (Evolution)
- [ ] Implement `lora_dataset.py` for structured LoRA fine-tuning exports.
- [ ] **Goal**: Readying data for the next jump in base intelligence.

---
*Mini Jules: Evolving into your personal engineering brain.*
