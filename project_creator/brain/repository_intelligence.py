from .architecture_extractor import ArchitectureExtractor
from .call_graph_learner import CallGraphLearner


class RepositoryIntelligence:
    """
    High-level repository understanding layer.
    """

    def __init__(self, project_root: str):
        self.root = project_root
        self.call_graph = CallGraphLearner(project_root)
        self.arch_extractor = ArchitectureExtractor()

    def generate_intelligence_summary(self):
        print(f"🧠 [INTEL] Analyzing repository at {self.root}")

        # 1. Structure
        structure = self.arch_extractor.extract_structure(self.root)
        arch_type = self.arch_extractor.identify_arch_type(structure)

        # 2. Call Graph (AST)
        self.call_graph.build_graph()

        return {
            "architecture_type": arch_type,
            "modules": structure["modules"],
            "impact_map": "Available via call_graph.get_impacted_files",
            "summary": f"A {arch_type} project with {len(structure['modules'])} modules.",
        }
