import faiss
import numpy as np
import os
import json
from sentence_transformers import SentenceTransformer

class VectorStore:
    def __init__(self, index_path):
        self.index_path = index_path
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        self._load()

    def add(self, text, meta):
        embedding = self.model.encode([text])
        self.index.add(np.array(embedding).astype('float32'))
        self.metadata.append(meta)
        self._save()

    def search(self, query, top_k=5):
        if self.index.ntotal == 0: return []
        embedding = self.model.encode([query])
        distances, indices = self.index.search(np.array(embedding).astype('float32'), top_k)

        results = []
        for i in indices[0]:
            if i != -1 and i < len(self.metadata):
                results.append(self.metadata[i])
        return results

    def _save(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.index_path + ".meta", 'w') as f:
            json.dump(self.metadata, f)

    def _load(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.index_path + ".meta", 'r') as f:
                self.metadata = json.load(f)
