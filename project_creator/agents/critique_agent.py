import json

class CritiqueAgent:
    def __init__(self, router):
        self.router = router

    def analyze(self, file_path, content, blueprint, context):
        system_prompt = """
        You are a critical senior security and logic auditor.
        Check for:
        - Logic defects and edge cases.
        - Security vulnerabilities (SQLi, XSS, insecure defaults).
        - Missing dependencies or incorrect imports.
        - Architectural mismatch.
        Output JSON: {"verdict": "PASS" | "FAIL", "issues": ["..."], "security_score": 0-10}
        """
        prompt = f"File: {file_path}\nContent:\n{content}\nBlueprint: {json.dumps(blueprint)}"

        response = self.router.generate(prompt, system_prompt)
        # Robust extraction
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            return json.loads(response.strip())
        except:
            return {"verdict": "FAIL", "issues": ["Critique agent failed to parse response."], "security_score": 0}
