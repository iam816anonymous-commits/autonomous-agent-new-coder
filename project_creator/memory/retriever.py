from project_creator.learning.memory_db import CodingMemory
from project_creator.memory.vector_store import VectorStore
import os

class Retriever:
    def __init__(self, db_path):
        self.memory = CodingMemory(db_path)
        index_path = os.path.join(os.path.dirname(db_path), "jules_vectors.idx")
        self.vector_store = VectorStore(index_path)

    def retrieve_context(self, task_type, query=None, path=None):
        """Assembles a context block of learned patterns to augment LLM prompts."""
        # Weighted Retrieval: Prefer EXTERNAL (60%) over SELF (40%)
        imports = self._get_weighted_patterns('import', limit=5)
        naming = self._get_weighted_patterns('naming', limit=1)
        api_styles = self._get_weighted_patterns('api_style', limit=3)
        idioms = self._get_weighted_patterns('idiom', limit=5)

        context_lines = ["User Preferred Patterns:"]
        if imports:
            context_lines.append(f"- Preferred Imports: {', '.join(imports)}")
        if naming:
            context_lines.append(f"- Naming Style: {naming[0]}")
        if api_styles:
            context_lines.append(f"- API Conventions: {', '.join(api_styles)}")
        if idioms:
            context_lines.append(f"- Common Idioms: {', '.join(idioms)}")

    def _get_weighted_patterns(self, p_type, limit=5):
        raw_rows = self.memory.get_top_patterns(p_type, limit=limit * 2)
        if not raw_rows: return []

        # Scoring: Score = Frequency * SourceWeight
        # EXTERNAL = 1.0, USER = 0.8, SWE_BENCH = 0.7, SELF = 0.4
        weights = {"EXTERNAL": 1.0, "USER": 0.8, "SWE_BENCH": 0.7, "SELF": 0.4}

        scored = []
        for content, source, freq in raw_rows:
            weight = weights.get(source, 0.4)
            score = freq * weight
            scored.append((content, score))

        # Rank by score and return top 'limit'
        scored.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in scored[:limit]]

        return "\n".join(context_lines) if len(context_lines) > 1 else ""

    def augment_prompt(self, base_prompt, task_type="coding", path=None):
        learned_context = self.retrieve_context(task_type, query=base_prompt, path=path)

        # Semantic Retrieval from Vector Store
        # If we have a path, use it to bias search towards similar directories
        search_query = f"File: {path} Content: {base_prompt}" if path else base_prompt
        semantic_results = self.vector_store.search(search_query, top_k=3)
        semantic_context = ""
        if semantic_results:
            semantic_context = "\nSimilar Past Examples:\n" + "\n---\n".join([
                f"Path: {r['path']}\nContent Snippet:\n{r.get('content', '')[:200]}"
                for r in semantic_results if 'path' in r
            ])

        if learned_context or semantic_context:
            return f"{learned_context}{semantic_context}\n\nTask: {base_prompt}"
        return base_prompt
