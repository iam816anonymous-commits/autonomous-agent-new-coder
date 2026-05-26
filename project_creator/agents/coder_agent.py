import json

class CoderAgent:
    def __init__(self, router):
        self.router = router

    def generate_file(self, file_path, description, blueprint, context):
        system_prompt = "You are a senior developer. Write full, production-ready source code. No explanations, no markdown blocks."
        prompt = f"Blueprint: {json.dumps(blueprint)}\nFile: {file_path}\nDescription: {description}\nContext: {list(context.keys())}"

        content = self.router.generate(prompt, system_prompt)
        # Clean markdown
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"): lines = lines[1:]
            if lines and lines[-1].startswith("```"): lines = lines[:-1]
            content = "\n".join(lines).strip()
        return content
