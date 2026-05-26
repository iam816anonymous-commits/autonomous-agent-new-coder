import json

class CoderAgent:
    def __init__(self, router, memory=None):
        self.router = router
        self.memory = memory

    def generate_code(self, file_path, description, blueprint, context_files):
        # Incorporate user preferences into the system prompt
        preferences = self.memory.get_preferences() if self.memory else {}
        pref_str = "\n".join([f"- {k}: {v}" for k, v in preferences.items()])

        system_prompt = f"""
        You are a senior software engineer. Write full, production-ready source code.

        User Preferences & Styles:
        {pref_str if pref_str else "Standard clean code practices."}

        No explanations, no markdown blocks.
        """

        context_str = "\n".join([f"File: {path}\nContent:\n{content}\n---" for path, content in context_files.items()])

        prompt = f"""
        Project Blueprint: {json.dumps(blueprint)}
        File: {file_path}
        Description: {description}

        Context:
        {context_str}
        """

        content = self.router.generate(prompt, system_prompt)

        # Clean up markdown
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        return content
