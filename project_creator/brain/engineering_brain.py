from .architecture_memory import ArchitectureMemory
from .pattern_memory import PatternMemory
from .repair_memory import RepairMemory
from .semantic_search import SemanticSearch
from .strategy_builder import StrategyBuilder

class EngineeringBrain:
    def __init__(self, db_path):
        self.db_path = db_path
        self.arch_memory = ArchitectureMemory(db_path)
        self.pattern_memory = PatternMemory(db_path)
        self.repair_memory = RepairMemory(db_path)
        self.search = SemanticSearch(db_path)
        self.strategy_builder = StrategyBuilder(self)

    def consult(self, goal: str):
        """
        Retrieves context and builds a strategy before planning.
        """
        print(f"🧠 Brain: Consulting on goal: {goal}")

        similar_projects = self.search.find_similar_projects(goal)
        arch_rec = self.arch_memory.retrieve_recommendation(goal)
        patterns = self.pattern_memory.get_best_patterns('api_style')
        idioms = self.pattern_memory.get_idioms()

        context = {
            "similar_projects": [p['path'] for p in similar_projects],
            "recommended_arch": arch_rec[0]['architecture'] if arch_rec else "Modular",
            "recommended_deps": arch_rec[0].get('deps', []) if arch_rec else [],
            "failure_patterns": ["Circular imports", "Hardcoded credentials"],
            "idioms": idioms
        }

        doc, data = self.strategy_builder.build_strategy(goal, context)
        return doc, data

    def learn_from_experience(self, session_data):
        """
        Extracts lessons from a completed project.
        """
        print("🧠 Brain: Extracting lessons from experience...")
        # 1. Update Architecture Memory
        self.arch_memory.store_architecture(
            project_type="custom",
            architecture=session_data.get('blueprint', {}).get('architecture', 'Modular'),
            deps=[],
            success_score=1.0
        )

        # 2. Extract Repair Patterns
        for repair in session_data.get('repairs', []):
            self.repair_memory.store_repair(
                error=repair['issue'],
                traceback="",
                root_cause="Logic error",
                repair=repair['patch']
            )
