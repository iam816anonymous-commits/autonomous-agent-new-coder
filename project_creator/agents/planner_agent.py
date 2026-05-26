from project_creator.core.utils import extract_json

class PlannerAgent:
    def __init__(self, router):
        self.router = router

    def create_blueprint(self, user_prompt):
        system_prompt = """
        You are a senior software architect. Generate a structured multi-file project blueprint.
        Include modules (backend, frontend, etc.) and file paths.
        Output valid JSON only.
        """
        response = self.router.generate_blueprint(user_prompt, system_prompt)
        return extract_json(response)
