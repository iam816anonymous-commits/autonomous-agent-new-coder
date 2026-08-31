# Semantic Graph Model

## 1. Node & Edge Representations
The `SemanticRepositoryGraph` models repository structures using deterministic in-memory graphs:
* **Nodes**: `SemanticSymbol` (`MODULE`, `CLASS`, `FUNCTION`, `METHOD`, `VARIABLE`, `IMPORT`, `ROUTE`).
* **Edges**: `SemanticRelation` (`DEFINES`, `REFERENCES`, `CALLS`, `INHERITS`, `CONTAINS`, `ROUTES_TO`). Each relation carries evidence tracking line numbers and extraction mechanisms.
