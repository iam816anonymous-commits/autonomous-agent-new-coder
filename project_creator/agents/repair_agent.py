import json

class RepairAgent:
    def __init__(self, router):
        self.router = router

    def propose_patch(self, file_path, content, critique, blueprint, context):
        system_prompt = """
        You are a senior developer. Propose a patch to fix identified issues.
        Output valid JSON only:
        {
          "file": "path",
          "reason": "why",
          "action": "repair",
          "new_content": "corrected code"
        }
        """
        prompt = f"File: {file_path}\nCritique: {critique}\nOriginal Content:\n{content}"

        response = self.router.generate(prompt, system_prompt)
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
