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

class RepairAgent:
    def __init__(self, router):
        self.router = router

    def repair(self, file_path, content, critique, blueprint, context):
        system_prompt = "You are a senior developer. Fix the issues identified in the critique. Output ONLY corrected code."
        prompt = f"File: {file_path}\nCritique: {critique}\nOriginal Content:\n{content}"

        repaired = self.router.generate(prompt, system_prompt)
        if repaired.startswith("```"):
            lines = repaired.splitlines()
            if lines[0].startswith("```"): lines = lines[1:]
            if lines and lines[-1].startswith("```"): lines = lines[:-1]
            repaired = "\n".join(lines).strip()
        return repaired
