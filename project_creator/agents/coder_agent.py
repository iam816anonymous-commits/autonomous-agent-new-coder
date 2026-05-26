import json

class CoderAgent:
    def __init__(self, router):
        self.router = router

    def generate_file(self, file_path, description, blueprint, context):
        system_prompt = """
        You are an elite senior software engineer. Write high-quality, production-ready source code.
        Requirements:
        - Include proper error handling and logging.
        - Use type hints and docstrings.
        - Follow security best practices (no hardcoded secrets).
        - Ensure architectural consistency with existing project files.
        - Output ONLY source code, no markdown blocks, no explanations.
        """

        context_str = "\n".join([f"File: {p}\nContent:\n{c}\n---" for p, c in context.items()])

        prompt = f"""
        Blueprint: {json.dumps(blueprint)}
        File Path: {file_path}
        Description: {description}

        Existing Project Context:
        {context_str if context_str else "Starting fresh."}

        Generate the implementation for {file_path}.
        """

        content = self.router.generate(prompt, system_prompt)
        # Final safety: strip markdown if the model fails to follow instruction
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"): lines = lines[1:]
            if lines and lines[-1].startswith("```"): lines = lines[:-1]
            content = "\n".join(lines).strip()
        return content
