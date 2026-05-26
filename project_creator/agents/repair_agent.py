class CritiqueAgent:
    def __init__(self, router):
        self.router = router

    def analyze(self, file_path, content, context_files):
        system_prompt = "You are a critical code reviewer. Identify bugs, security issues, or missing imports. Output 'PASS' if ok, otherwise list issues."

        prompt = f"File: {file_path}\nContent:\n{content}\n\nContext files available for reference."

        return self.router.generate(prompt, system_prompt)

class RepairAgent:
    def __init__(self, router):
        self.router = router

    def repair(self, file_path, content, critique, context_files):
        system_prompt = "You are a senior developer. Fix the issues identified in the critique. Output ONLY the corrected source code."

        prompt = f"File: {file_path}\nOriginal Content:\n{content}\nCritique:\n{critique}"

        repaired = self.router.generate(prompt, system_prompt)

        if repaired.startswith("```"):
            lines = repaired.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            repaired = "\n".join(lines).strip()

        return repaired
