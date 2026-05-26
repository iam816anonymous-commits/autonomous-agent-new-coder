import json

class CoderAgent:
    def __init__(self, router):
        self.router = router

    def generate_code(self, file_path, description, blueprint, context_files):
        system_prompt = "You are a senior software engineer. Write full, production-ready source code. No explanations, no markdown blocks."

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
