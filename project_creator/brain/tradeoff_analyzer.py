from typing import Dict, Any

class TradeoffAnalyzer:
    """
    Analyzes architectural recommendations for benefits, risks, and costs.
    """
    def analyze(self, recommendation: Dict[str, Any]) -> Dict[str, Any]:
        style = recommendation.get('base_architecture', recommendation.get('architecture_style', 'Standard'))
        patterns = recommendation.get('merged_patterns', recommendation.get('suggested_patterns', []))

        analysis = {
            "benefits": self._get_benefits(style, patterns),
            "risks": self._get_risks(style, patterns),
            "complexity": "Medium" if len(patterns) < 5 else "High",
            "maintenance_cost": "Low" if "Modular" in style else "Medium",
            "scalability_impact": "High" if "Microservices" in style or "Async" in str(patterns) else "Normal"
        }

        return analysis

    def _get_benefits(self, style, patterns):
        benefits = [f"Leverages proven {style} structure"]
        if "Agent" in str(patterns):
            benefits.append("Autonomous task execution capabilities")
        if "RAG" in str(patterns):
            benefits.append("Semantic knowledge retrieval")
        return benefits

    def _get_risks(self, style, patterns):
        risks = []
        if "Monolith" in style:
            risks.append("Potential scaling bottlenecks")
        if len(patterns) > 10:
            risks.append("Pattern overload / high cognitive load")
        return risks
