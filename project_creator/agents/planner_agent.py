import json

class PlannerAgent:
    def __init__(self, router):
        self.router = router

    def create_blueprint(self, user_prompt):
        system_prompt = """
        You are a senior software architect. Based on the user requirement, generate a structured multi-file project blueprint.
        The blueprint must include:
        - project_name
        - modules: (e.g., backend, frontend, docs, tests)
        - files: a list of objects with {"path": "module/file.py", "description": "purpose"}

        Output valid JSON only.
        """
        # Use specialized blueprint generator for reliable JSON/Context
        response = self.router.generate_blueprint(user_prompt, system_prompt)
        return self._extract_json(response)

    def _extract_json(self, text):
        try:
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
        except:
            return None
