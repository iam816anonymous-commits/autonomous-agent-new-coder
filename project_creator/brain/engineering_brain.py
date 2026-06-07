from .architecture_memory import ArchitectureMemory
from .architecture_extractor import ArchitectureExtractor
from .pattern_memory import PatternMemory
from .repair_memory import RepairMemory
from .repository_memory import RepositoryMemory
from .strategy_builder import StrategyBuilder
from .architecture_consultant import ArchitectureConsultant
from .repository_comparison import RepositoryComparison
from .architecture_synthesizer import ArchitectureSynthesizer
from .tradeoff_analyzer import TradeoffAnalyzer
import os

class EngineeringBrain:
    def __init__(self, db_path):
        self.arch_memory = ArchitectureMemory(db_path)
        self.extractor = ArchitectureExtractor()
        self.pattern_memory = PatternMemory(db_path)
        self.repair_memory = RepairMemory(db_path)
        self.repo_memory = RepositoryMemory(db_path)
        self.strategy_builder = StrategyBuilder(self)

        # Architecture Intelligence Modules
        self.consultant = ArchitectureConsultant(db_path)
        self.comparison = RepositoryComparison()
        self.synthesizer = ArchitectureSynthesizer()
        self.tradeoffs = TradeoffAnalyzer()

    def consult(self, goal):
        """
        Retrieves memory and builds the Strategy Document.
        """
        print(f"🧠 Brain: Consulting on goal '{goal}'")

        # Retrieval
        sim_arch = self.arch_memory.retrieve_similar(goal)
        sim_repairs = self.repair_memory.retrieve_repairs(goal)
        sim_repos = self.repo_memory.retrieve_relevant(goal)

        context = {
            "recommended_arch": sim_arch[0].get('architecture') if sim_arch else "Standard Modular",
            "recommended_deps": sim_arch[0].get('dependencies', []) if sim_arch else [],
            "failure_patterns": [r.get('error') for r in sim_repairs if r.get('success_rate', 1.0) < 0.5],
            "repair_strategies": [r.get('repair') for r in sim_repairs if r.get('success_rate', 0.0) > 0.7],
            "relevant_repos": [r.get('repository') for r in sim_repos],
            "repository_knowledge": sim_repos
        }

        # 1. Advanced Architecture Intelligence
        recommendation = self.consultant.recommend(goal)
        tradeoff_analysis = self.tradeoffs.analyze(recommendation)

        context["architectural_recommendation"] = recommendation
        context["tradeoffs"] = tradeoff_analysis

        strategy_doc = self.strategy_builder.generate_strategy_document(goal, context)

        # 2. Design Review Artifact
        self._generate_design_review(goal, recommendation, tradeoff_analysis)

        return strategy_doc, context

    def get_self_architecture(self):
        """Returns the high-level architecture of Jules itself."""
        return self.extractor.extract_structure(".")

    def _generate_design_review(self, goal, recommendation, tradeoffs):
        report = f"""# 📐 Architecture Review: {goal}

## 🏗️ Recommended Structure
- **Style**: {recommendation['architecture_style']}
- **Core Patterns**: {', '.join(recommendation['suggested_patterns'][:5])}
- **References**: {', '.join(recommendation['external_references'])}

## ⚖️ Tradeoff Analysis
- **Benefits**: {', '.join(tradeoffs['benefits'])}
- **Risks**: {', '.join(tradeoffs['risks']) if tradeoffs['risks'] else 'Low known risks'}
- **Complexity**: {tradeoffs['complexity']}
- **Maintenance Cost**: {tradeoffs['maintenance_cost']}

## 🛡️ Security & Reliability
- **Known Pitfalls**: {', '.join(recommendation['known_pitfalls']) if recommendation['known_pitfalls'] else 'None identified'}
"""
        with open("architecture_review.md", "w") as f:
            f.write(report)

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
