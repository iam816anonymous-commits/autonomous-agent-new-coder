from .base_memory import BaseBrainMemory


class RepositoryMemory(BaseBrainMemory):
    """
    Stores high-level 'Knowledge Cards' for indexed repositories.
    """

    def __init__(self, db_path):
        super().__init__(db_path, index_name="repository")

    def store_card(self, card):
        """Stores a JSON knowledge card and indexes it semantically."""
        repo_name = card.get("repository", "unknown")
        category = card.get("category", "Generic")
        arch = card.get("architecture", "Standard")

        # Build searchable context
        text_context = [
            f"Repository: {repo_name}",
            f"Category: {category}",
            f"Architecture: {arch}",
            f"Patterns: {', '.join(card.get('patterns', []))}",
            f"Frameworks: {', '.join(card.get('frameworks', []))}",
        ]

        self.vector_store.add("\n".join(text_context), card)

    def retrieve_relevant(self, goal, top_k=2):
        """Searches for repository cards relevant to a project goal."""
        return self.search(goal, top_k=top_k)
