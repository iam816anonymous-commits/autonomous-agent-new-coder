# Bolt's Journal

## 2025-05-15 - [Model Cache for SentenceTransformer]
**Learning:** Initializing SentenceTransformer in every VectorStore instance adds significant overhead (~1.4s per instantiation) and redundant memory usage. Using a class-level cache reduces instantiation to <0.002s.
**Action:** Always cache expensive ML model loads at the class level when multiple instances of the consumer are expected.
