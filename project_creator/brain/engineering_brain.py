from .architecture_memory import ArchitectureMemory
from .pattern_memory import PatternMemory
from .repair_memory import RepairMemory
from .strategy_builder import StrategyBuilder
import os

class EngineeringBrain:
    def __init__(self, db_path):
        self.arch_memory = ArchitectureMemory(db_path)
        self.pattern_memory = PatternMemory(db_path)
        self.repair_memory = RepairMemory(db_path)
        self.strategy_builder = StrategyBuilder(self)

    def consult(self, goal):
        """
        Retrieves memory and builds the Strategy Document.
        """
        print(f"🧠 Brain: Consulting on goal '{goal}'")

        # Retrieval
        sim_arch = self.arch_memory.retrieve_similar(goal)
        sim_repairs = self.repair_memory.retrieve_repairs(goal)

        context = {
            "recommended_arch": sim_arch[0].get('architecture') if sim_arch else "Standard Modular",
            "recommended_deps": sim_arch[0].get('dependencies', []) if sim_arch else [],
            "failure_patterns": [r.get('error') for r in sim_repairs if r.get('success_rate', 1.0) < 0.5],
            "repair_strategies": [r.get('repair') for r in sim_repairs if r.get('success_rate', 0.0) > 0.7]
        }

        strategy_doc = self.strategy_builder.generate_strategy_document(goal, context)
        return strategy_doc

    def learn_from_completed_task(self, session_data):
        """
        Self-Learning: Updates memories after a successful project.
        """
        print("🧠 Brain: Extracting lessons from completed task...")
        # (This is triggered by Orchestrator after project completion)

        # 1. Update Architecture
        blueprint = session_data.get('blueprint', {})
        self.arch_memory.store_architecture(
            project_type=blueprint.get('type', 'custom'),
            architecture=blueprint.get('architecture', 'modular'),
            dependencies=[] # Extracted from manifest in real impl
        )

        # 2. Update Repairs
        for repair in session_data.get('repairs', []):
            self.repair_memory.store_repair(
                error=repair['issue'],
                traceback="",
                root_cause="Logic error detected during dry-run",
                repair=repair['patch']
            )
