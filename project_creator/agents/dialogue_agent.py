import json

class DialogueAgent:
    """
    Orchestrates a multi-turn conversation to gather detailed requirements.
    """
    def __init__(self, router):
        self.router = router
        self.questions = [
            "What is the primary objective of this project?",
            "Who are the intended users?",
            "What are the core features required?",
            "Are there any specific tech stack preferences (e.g., database, frontend framework)?",
            "What are the key security requirements?",
            "Do you have specific testing or CI/CD expectations?",
            "Are there any existing constraints or external APIs to integrate?"
        ]
        self.answers = {}

    def gather_requirements(self, initial_goal):
        print(f"\n💬 Dialogue Agent: Gathering requirements for '{initial_goal}'")
        self.answers["initial_goal"] = initial_goal

        for i, q in enumerate(self.questions):
            try:
                # In a real CLI, we use input(). For automated agents, we might mock this.
                ans = input(f"[{i+1}/7] {q}\n> ")
                self.answers[f"q{i+1}"] = ans
            except EOFError:
                self.answers[f"q{i+1}"] = "No specific preference."

        # Summarize requirements using LLM
        summary_prompt = f"Summarize these project requirements into a structured JSON:\n{json.dumps(self.answers)}"
        system_prompt = "You are a senior business analyst. Extract structured requirements."

        response = self.router.generate(summary_prompt, system_prompt)
        from project_creator.core.utils import extract_json
        return extract_json(response)

    def validate_architecture(self, architecture_blueprint):
        """Validates the blueprint against gathered requirements."""
        prompt = f"Requirements: {json.dumps(self.answers)}\nBlueprint: {json.dumps(architecture_blueprint)}\nDoes this blueprint satisfy all requirements? Return PASS/FAIL and reason."
        response = self.router.generate(prompt, "You are a quality assurance architect.")
        return response

    def refine_requirements(self, feedback):
        """Updates internal requirements based on user feedback."""
        self.answers["feedback"] = feedback
        print("✅ Requirements refined.")
        return self.answers
