import json

class CritiqueAgent:
    def __init__(self, router):
        self.router = router

    def analyze(self, file_path, content, blueprint, context):
        system_prompt = """
        You are a critical code reviewer. Check for:
        - Missing imports
        - Broken paths
        - Dependency errors
        - Architecture mismatch with the blueprint
        Output 'PASS' if perfect, otherwise list issues.
        """
        prompt = f"File: {file_path}\nContent:\n{content}\nBlueprint: {json.dumps(blueprint)}"
        return self.router.generate(prompt, system_prompt)
