from typing import Dict

from project_creator.brain.call_graph_learner import CallGraphLearner


class RepairStrategist:
    """
    Determines the best repair strategy based on failure context.
    """

    def __init__(self, repair_agent, error_classifier, project_root=None):
        self.repair_agent = repair_agent
        self.error_classifier = error_classifier
        self.project_root = project_root
        self.call_graph = CallGraphLearner(project_root) if project_root else None

    from typing import Optional

    def formulate_repair(
        self,
        path: str,
        content: str,
        issues: list,
        blueprint: Dict,
        generated_files: Dict,
        extra_context: Optional[str] = None,
    ):
        print(f"🛠️  Strategizing repair for {path}...")

        # 1. Classification
        error_msg = str(issues)
        cat, sev = self.error_classifier.classify_error(error_msg)
        plan = self.error_classifier.get_repair_plan(cat)

        # 2. Impact Analysis (AST-based)
        impacted = []
        if self.call_graph:
            self.call_graph.build_graph()
            impacted = self.call_graph.get_impacted_files(path)

        impact_warning = (
            f"\n⚠️  WARNING: Changes to {path} may affect: {', '.join(impacted)}"
            if impacted
            else ""
        )

        # 3. Combine classifier plan with agent proposing
        augmented_context = (
            f"REPAIR STRATEGY: {plan}{impact_warning}\n\n{extra_context}"
            if extra_context
            else f"REPAIR STRATEGY: {plan}{impact_warning}"
        )

        return self.repair_agent.propose_patch(
            path,
            content,
            issues,
            blueprint,
            generated_files,
            extra_context=augmented_context,
        )
