import json

class AuditAgent:
    def __init__(self, router):
        self.router = router

    def perform_full_audit(self, file_path, content, context_files):
        audit_types = ["security", "performance", "cost", "dependency", "dead_code"]
        results = {}

        for atype in audit_types:
            system_prompt = f"You are a specialist in {atype} auditing. Review the following code and list any issues found."
            prompt = f"File: {file_path}\nContent:\n{content}"
            results[atype] = self.router.generate(prompt, system_prompt)

        return results

class RepairAgent:
    def __init__(self, router):
        self.router = router

    def propose_patch(self, file_path, old_content, critique, context_files):
        system_prompt = """
        You are a senior developer. Propose a structured patch in JSON format.
        Structure:
        {
          "file": "path",
          "reason": "why",
          "risk": "low/medium/high",
          "tests": ["test_name"],
          "new_content": "full source code"
        }
        """
        prompt = f"File: {file_path}\nOriginal Content:\n{old_content}\nCritique:\n{critique}"

        response = self.router.generate(prompt, system_prompt)

        try:
            patch = json.loads(self._extract_json(response))
            patch['old_content'] = old_content
            # We will generate diff separately or ask model for it if preferred
            return patch
        except Exception as e:
            print(f"Error parsing patch JSON: {e}")
            return None

    def _extract_json(self, text):
        if "```json" in text:
            return text.split("```json")[1].split("```")[0]
        elif "```" in text:
            return text.split("```")[1].split("```")[0]
        return text.strip()
