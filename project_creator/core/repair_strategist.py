from typing import Dict, Any

class RepairStrategist:
    """
    Determines the best repair strategy based on failure context.
    """
    def __init__(self, repair_agent, error_classifier):
        self.repair_agent = repair_agent
        self.error_classifier = error_classifier

    def formulate_repair(self, path: str, content: str, issues: list, blueprint: Dict, generated_files: Dict, extra_context: str = None):
        print(f"🛠️  Strategizing repair for {path}...")

        # Classification
        error_msg = str(issues)
        cat, sev = self.error_classifier.classify_error(error_msg)
        plan = self.error_classifier.get_repair_plan(cat)

        # Combine classifier plan with agent proposing
        augmented_context = f"REPAIR STRATEGY: {plan}\n\n{extra_context}" if extra_context else f"REPAIR STRATEGY: {plan}"

        return self.repair_agent.propose_patch(path, content, issues, blueprint, generated_files, extra_context=augmented_context)
