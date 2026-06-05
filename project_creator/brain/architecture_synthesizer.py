from typing import Dict, List, Any

class ArchitectureSynthesizer:
    """
    Synthesizes a master architecture from multiple source repository cards.
    """
    def synthesize(self, repos: List[Dict[str, Any]], goal: str) -> Dict[str, Any]:
        if not repos:
            return {"error": "No repositories provided for synthesis."}

        all_patterns = []
        all_deps = []
        for r in repos:
            all_patterns.extend(r.get('patterns', []))
            all_deps.extend(r.get('dependencies', []))

        # Top 5 most frequent patterns (heuristic weighting)
        from collections import Counter
        top_patterns = [p for p, _ in Counter(all_patterns).most_common(5)]

        # Assemble recommended architecture
        synthesis = {
            "target_goal": goal,
            "base_architecture": self._primary_style(repos),
            "merged_patterns": list(set(top_patterns)),
            "core_stack": list(set(all_deps))[:10], # Top 10 unique dependencies
            "recommendation": f"Assembled from {', '.join([r.get('repository') for r in repos])}"
        }

        return synthesis

    def _primary_style(self, repos):
        styles = [r.get('architecture') for r in repos]
        if not styles: return "Standard Modular"
        from collections import Counter
        return Counter(styles).most_common(1)[0][0]
