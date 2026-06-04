from project_creator.core.utils import extract_json

class RepairAgent:
    def __init__(self, router):
        self.router = router

    def propose_patch(self, file_path, content, critique, blueprint, context, extra_context=None):
        system_prompt = """
        You are a senior developer. Propose a structured patch in JSON.
        Output schema: { "file": "path", "reason": "why", "status": "pending", "new_content": "code" }
        """
        prompt = f"File: {file_path}\nCritique: {critique}\nOriginal:\n{content}"
        if extra_context:
            prompt = f"Engineering Strategy:\n{extra_context}\n\n{prompt}"

        response = self.router.generate(prompt, system_prompt)
        return extract_json(response)
