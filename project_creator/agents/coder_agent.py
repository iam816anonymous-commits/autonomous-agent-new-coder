import json

class CoderAgent:
    def __init__(self, router):
        self.router = router

    def generate_file(self, file_path, description, blueprint, context):
        system_prompt = "You are a senior developer. Write full, production-ready source code. No explanations, no markdown blocks."

        # Incremental assembly: Feed full code content back into the context
        context_str = "\n".join([f"File: {p}\nContent:\n{c}\n---" for p, c in context.items()])

        prompt = f"""
        Project Blueprint: {json.dumps(blueprint)}

        File to generate: {file_path}
        Description: {description}

        Current Project Context:
        {context_str if context_str else "No files generated yet."}

        Provide only the source code for {file_path}.
        """

        content = self.router.generate(prompt, system_prompt)
        # Clean markdown
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"): lines = lines[1:]
            if lines and lines[-1].startswith("```"): lines = lines[:-1]
            content = "\n".join(lines).strip()
        return content
