import json
from project_creator.memory.retriever import Retriever
from project_creator.learning import DB_PATH

class CoderAgent:
    def __init__(self, router):
        self.router = router
        self.retriever = Retriever(DB_PATH)

    def generate_file(self, file_path, description, blueprint, context, strategy_doc=None):
        system_prompt = """
        You are an elite senior software engineer with a focus on CYBERSECURITY.

        Security Constitution:
        - NO hardcoded secrets or environment variables.
        - NO use of insecure libraries (e.g. pickle, marshal).
        - VALIDATE all user input to prevent injection (SQLi, XSS).
        - USE secure defaults (e.g. constant-time comparisons for passwords).

        Coding Standards:
        - High-quality, production-ready code with type hints and docstrings.
        - Robust error handling and informative logging.
        - Maintain absolute architectural parity.

        Output ONLY source code. No markdown. No chatter.
        """

        context_str = "\n".join([f"File: {p}\nContent:\n{c}\n---" for p, c in context.items()])

        strategy_context = f"STRATEGY:\n{strategy_doc}\n\n" if strategy_doc else ""
        prompt = f"{strategy_context}Blueprint: {json.dumps(blueprint)}\nTarget: {file_path}\nGoal: {description}\nContext:\n{context_str}"

        # Augment with learned style and path-aware context
        prompt = self.retriever.augment_prompt(prompt, task_type="coding", path=file_path)

        content = self.router.generate(prompt, system_prompt)
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"): lines = lines[1:]
            if lines and lines[-1].startswith("```"): lines = lines[:-1]
            content = "\n".join(lines).strip()
        return content
