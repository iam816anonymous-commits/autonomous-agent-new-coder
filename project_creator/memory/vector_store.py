import json
import os

import faiss
import numpy as np

try:
    from sentence_transformers import SentenceTransformer

    HAS_SEMANTIC = True
except ImportError:
    HAS_SEMANTIC = False


class VectorStore:
    _model_cache = None  # Class-level cache to avoid redundant loads

    def __init__(self, index_path):
        self.index_path = index_path
        self.model = None
        self.dimension = 384
        self.index = None
        self.metadata = []

        if HAS_SEMANTIC:
            try:
                # ⚡ Bolt Optimization: Use class-level cache for SentenceTransformer
                if VectorStore._model_cache is None:
                    VectorStore._model_cache = SentenceTransformer("all-MiniLM-L6-v2")
                self.model = VectorStore._model_cache

                self.index = faiss.IndexFlatL2(self.dimension)
                self._load()
            except:
                print("⚠️  VectorStore: Failed to initialize FAISS index.")

    def add(self, text, meta, auto_save=True):
        if not self.model or self.index is None:
            return
        embedding = self.model.encode([text])
        self.index.add(np.array(embedding).astype("float32"))
        self.metadata.append(meta)
        if auto_save:
            self._save()

    def add_batch(self, texts, metadatas):
        """P2-10: Batch persistence for high-volume ingestion."""
        if not self.model or self.index is None or not texts:
            return
        embeddings = self.model.encode(texts)
        self.index.add(np.array(embeddings).astype("float32"))
        self.metadata.extend(metadatas)
        self._save()

    def search(self, query, top_k=5):
        if not self.model or self.index is None or self.index.ntotal == 0:
            return []
        embedding = self.model.encode([query])
        distances, indices = self.index.search(
            np.array(embedding).astype("float32"), top_k
        )

        results = []
        for i in indices[0]:
            if i != -1 and i < len(self.metadata):
                results.append(self.metadata[i])
        return results

    def _save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.index_path + ".meta", "w") as f:
            json.dump(self.metadata, f)

    def _load(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.index_path + ".meta", "r") as f:
                self.metadata = json.load(f)
