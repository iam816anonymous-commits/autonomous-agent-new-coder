import json

class CoderAgent:
    def __init__(self, router):
        self.router = router

    def generate_file(self, file_path, description, blueprint, context):
        system_prompt = """
        You are an elite senior software engineer. Write high-quality, production-ready source code.
        Guidelines:
        - Use Type Hints and Docstrings.
        - Implement robust Error Handling and Logging.
        - Follow Security Best Practices (no hardcoded secrets).
        - Ensure Architectural Parity with existing files.
        - Output ONLY source code, no markdown, no explanations.
        """

        context_str = "\n".join([f"File: {p}\nContent:\n{c}\n---" for p, c in context.items()])

        prompt = f"""
        Blueprint: {json.dumps(blueprint)}

        File to generate: {file_path}
        Description: {description}

        Existing Project Context:
        {context_str if context_str else "Project start."}

        Generate full implementation for {file_path}.
        """

        content = self.router.generate(prompt, system_prompt)
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"): lines = lines[1:]
            if lines and lines[-1].startswith("```"): lines = lines[:-1]
            content = "\n".join(lines).strip()
        return content
