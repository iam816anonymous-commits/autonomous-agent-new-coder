import json

class PlannerAgent:
    def __init__(self, router):
        self.router = router

    def create_blueprint(self, user_prompt, existing_structure=None):
        system_prompt = """
        You are a senior software architect. Generate a project blueprint in JSON format.
        Include ecosystem files (requirements.txt, README.md, etc.).
        Structure: {"project_name": "name", "files": [{"path": "path/to/file", "description": "desc"}]}
        """
        prompt = f"User Requirements: {user_prompt}\n"
        if existing_structure:
            prompt += f"Existing Structure: {json.dumps(existing_structure)}"

        response = self.router.generate_blueprint(prompt, system_prompt)
        try:
            return json.loads(response)
        except:
            # Basic extraction if JSON is wrapped in markdown
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            return json.loads(response)
