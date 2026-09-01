# Semantic Evidence Model

## 1. Machine-Readable Evidence
`SemanticEvidenceTracker` records machine-readable `Evidence` objects for every symbol definition and call relation:
* `file`: Relative file path
* `line`: Source line number
* `extraction_mechanism`: Extraction tool (`AST`, `HEURISTIC`)
* `confidence_reason`: Human/machine readable justification
* `metadata`: AST node attributes
