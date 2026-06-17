from project_creator.core.utils import extract_json


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
        prompt = f"File: {file_path}\nContent:\n{content}\nBlueprint: {blueprint}"

        response = self.router.generate(prompt, system_prompt)
        result = extract_json(response)
        if result:
            return result
        return {
            "verdict": "FAIL",
            "issues": ["Failed to parse critique response."],
            "security_score": 0,
        }
