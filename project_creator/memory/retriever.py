from project_creator.learning.memory_db import CodingMemory

class Retriever:
    def __init__(self, db_path):
        self.memory = CodingMemory(db_path)

    def retrieve_context(self, task_type):
        """Assembles a context block of learned patterns to augment LLM prompts."""
        imports = self.memory.get_top_patterns('import', limit=5)
        naming = self.memory.get_top_patterns('naming', limit=1)
        api_styles = self.memory.get_top_patterns('api_style', limit=3)

        context_lines = ["User Preferred Patterns:"]
        if imports:
            context_lines.append(f"- Preferred Imports: {', '.join(imports)}")
        if naming:
            context_lines.append(f"- Naming Style: {naming[0]}")
        if api_styles:
            context_lines.append(f"- API Conventions: {', '.join(api_styles)}")

        return "\n".join(context_lines) if len(context_lines) > 1 else ""

    def augment_prompt(self, base_prompt, task_type="coding"):
        learned_context = self.retrieve_context(task_type)
        if learned_context:
            return f"{learned_context}\n\nTask: {base_prompt}"
        return base_prompt
