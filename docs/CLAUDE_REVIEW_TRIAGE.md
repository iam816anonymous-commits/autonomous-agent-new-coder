# Claude Review Triage

| Finding | Location | Severity | Status | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **P0-1 Benchmark Fabrication** | `intelligence_score.py`, `validate_jules.py` | P0 | Accepted | Metrics are hardcoded/simulated. Need to pull from DB/telemetry. |
| **P0-2 Git Clone Injection** | `os_learner.py` | P0 | Accepted | `git clone` uses unvalidated URLs. Needs strict https://github.com/ filtering and --. |
| **P0-3 Safety Validation** | `core/orchestrator.py`, `core/storage.py` | P0 | Accepted | `is_safe_content()` is not enforced in the primary write path. |
| **P0-4 manual_review_needed bypass** | `core/orchestrator.py` | P0 | Accepted | `generate_with_dependency_order` applies files regardless of validation status. |
| **P1-5 Config lifecycle** | `core/config.py` | P1 | Accepted | `Config` class is instantiated multiple times. Needs singleton pattern. |
| **P1-6 Constitution Import Bug** | `learning/constitution.py` | P1 | Accepted | `os` module used in `is_learnable` but not imported. |
| **P1-7 CoderAgent Resilience** | `agents/coder_agent.py` | P1 | Accepted | Missing checks for None/empty responses from router. |
| **P1-8 ToolExecutor Matching** | `core/tools.py` | P1 | Accepted | Naive substring matching for forbidden patterns. Needs token-aware matching. |
| **P2-9 Vector Store Fragmentation** | `learning/pattern_learner.py`, `memory/retriever.py` | P2 | Accepted | Multiple indices (`jules_patterns.idx` vs `jules_vectors.idx`). Should be consolidated. |
| **P2-10 Persistence Efficiency** | `memory/vector_store.py` | P2 | Accepted | `_save()` called on every `add()`. Needs batch support for ingestion. |
| **P2-11 Storage Compliance** | System-wide | P2 | Accepted | Direct `open().write()` used instead of `Storage.write_file()`. |
| **P3-12 Self-Play Data Quality** | `exports/lora_dataset.py` | P3 | Accepted | Generic instructions in LoRA export. Needs actual task context. |
