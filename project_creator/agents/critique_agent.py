import json
from project_creator.core.utils import extract_json

class CritiqueAgent:
    def __init__(self, router):
        self.router = router

    def analyze(self, file_path, content, blueprint, context):
        system_prompt = """
        You are a senior critical engineer. Analyze the code for defects.
        You can request tool verification (e.g. pytest).
        Output JSON:
        {
          "verdict": "PASS" or "FAIL",
          "issues": [],
          "verification_command": "optional shell command"
        }
        """
        prompt = f"File: {file_path}\nContent:\n{content}"
        response = self.router.generate(prompt, system_prompt)
        return extract_json(response)
