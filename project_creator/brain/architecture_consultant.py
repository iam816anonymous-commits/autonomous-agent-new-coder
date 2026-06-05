from typing import Dict, List, Any
from .repository_memory import RepositoryMemory
from .architecture_memory import ArchitectureMemory
from .pattern_memory import PatternMemory
from .repair_memory import RepairMemory
from .architecture_synthesizer import ArchitectureSynthesizer

class ArchitectureConsultant:
    """
    High-level reasoning agent that recommends superior architectures
    by synthesizing knowledge from multiple repository sources.
    """
    def __init__(self, db_path: str):
        self.repo_mem = RepositoryMemory(db_path)
        self.arch_mem = ArchitectureMemory(db_path)
        self.pattern_mem = PatternMemory(db_path)
        self.repair_mem = RepairMemory(db_path)
        self.synthesizer = ArchitectureSynthesizer()

    def recommend(self, goal: str) -> Dict[str, Any]:
        """
        Synthesizes a recommendation from all memory types.
        """
        # 1. Retrieve Knowledge
        relevant_repos = self.repo_mem.retrieve_relevant(goal, top_k=3)
        past_archs = self.arch_mem.retrieve_similar(goal, top_k=2)
        relevant_repairs = self.repair_mem.retrieve_repairs(goal, top_k=3)

        # 2. Advanced Synthesis
        if len(relevant_repos) > 1:
            synthesis = self.synthesizer.synthesize(relevant_repos, goal)
            style = synthesis['base_architecture']
            patterns = synthesis['merged_patterns']
        else:
            style = self._determine_style(past_archs, relevant_repos)
            patterns = []
            for repo in relevant_repos:
                patterns.extend(repo.get('patterns', []))

        # 3. Formulate Recommendation
        recommendation = {
            "goal": goal,
            "architecture_style": style,
            "suggested_patterns": list(set(patterns)),
            "external_references": [r.get('repository') for r in relevant_repos],
            "known_pitfalls": [r.get('error') for r in relevant_repairs if r.get('success_rate', 0) < 0.5],
            "confidence": self._calculate_confidence(relevant_repos, past_archs)
        }

        return recommendation

    def _determine_style(self, past_archs, repos):
        if past_archs:
            return past_archs[0].get('architecture', 'Modular Monolith')
        if repos:
            return repos[0].get('architecture', 'Modular Monolith')
        return "Standard Modular"

    def _calculate_confidence(self, repos, archs):
        score = 0.5
        if repos: score += 0.2
        if archs: score += 0.2
        return min(1.0, score)
