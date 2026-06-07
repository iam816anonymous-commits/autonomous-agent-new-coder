from project_creator.core.utils import extract_json
from project_creator.memory.retriever import Retriever
from project_creator.learning import DB_PATH

class PlannerAgent:
    def __init__(self, router):
        self.router = router
        self.retriever = Retriever(DB_PATH)

    def create_blueprint(self, user_prompt, strategy_doc=None):
        system_prompt = """
        You are a senior software architect. Generate a structured HIERARCHICAL project blueprint.

        Structure:
        {
          "project_name": "...",
          "stages": [
            {
              "name": "Core Models",
              "files": [{"path": "...", "description": "..."}]
            },
            {
              "name": "API Layer",
              "files": [...]
            }
          ]
        }

        Strictly follow the provided Architecture Strategy if available.
        ALIGN with the modular architectural patterns found in your PERSONAL CODING BRAIN memory (e.g., specialized coordinators, central database layer).
        Output valid JSON only.
        """

        full_prompt = user_prompt
        if strategy_doc:
            full_prompt = f"ARCHITECTURAL STRATEGY:\n{strategy_doc}\n\nUSER GOAL: {user_prompt}"

        # Augment with learned style and preference patterns
        full_prompt = self.retriever.augment_prompt(full_prompt, task_type="planning")

        # Self-Architecture Awareness
        from project_creator.brain.engineering_brain import EngineeringBrain
        import json
        brain = EngineeringBrain(DB_PATH)
        self_arch = brain.get_self_architecture()
        full_prompt = f"SELF ARCHITECTURE CONTEXT:\n{json.dumps(self_arch)}\n\n{full_prompt}"

        response = self.router.generate_blueprint(full_prompt, system_prompt)
        return extract_json(response)
