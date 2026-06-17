import random


class TaskGenerator:
    def __init__(self, router):
        self.router = router
        self.topics = [
            "FastAPI",
            "Streamlit",
            "CLI",
            "RAG",
            "Scraper",
            "Unit Testing",
            "Refactoring",
            "Bug fixing",
        ]

    def generate_task(self):
        topic = random.choice(self.topics)
        difficulty = random.choice(["Junior", "Mid", "Senior"])

        system_prompt = (
            "You are a senior engineering manager. Generate a synthetic coding task."
        )
        prompt = f"""
        Generate a coding challenge for a {difficulty} developer.
        Topic: {topic}
        Format: JSON
        {{
          "id": "task_id",
          "problem": "detailed description",
          "constraints": ["...", "..."],
          "expected_output": "code structure description",
          "difficulty": "{difficulty}",
          "topic": "{topic}"
        }}
        """

        response = self.router.generate(prompt, system_prompt)
        # We assume resilient extraction exists in core utils
        try:
            from project_creator.core.utils import extract_json

            return extract_json(response)
        except:
            return None
