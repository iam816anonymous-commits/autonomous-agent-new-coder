# Phase I Limitations & Honest Disclosure

## 1. Static Analysis Boundaries
* Static analysis cannot resolve runtime dynamic reflection, monkey patching, or runtime type annotations.
* Incremental analysis is fallback-guarded; any divergence triggers full re-analysis.
* All semantic confidence scores are explainable and derived from AST evidence.
