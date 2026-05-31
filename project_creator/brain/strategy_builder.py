import json

class StrategyBuilder:
    def __init__(self, brain):
        self.brain = brain

    def build_strategy(self, goal, context):
        """
        Creates an explicit Strategy Document.
        """
        strategy = {
            "similar_projects": context.get('similar_projects', []),
            "recommended_architecture": context.get('recommended_arch', 'Modular Monolith'),
            "recommended_dependencies": context.get('recommended_deps', []),
            "known_failure_patterns": context.get('failure_patterns', []),
            "security_recommendations": [
                "Validate all inputs",
                "Use secure communication",
                "Sanitize file paths"
            ],
            "implementation_strategy": "Plan-first, then build core modules followed by integration."
        }

        # Format as Markdown Strategy Document
        doc = f"""# 📑 Strategy Document: {goal}

## 🏗️ Recommended Architecture
{strategy['recommended_architecture']}

## 📦 Key Dependencies
{', '.join(strategy['recommended_dependencies'])}

## 🛡️ Security & Quality Focus
- {strategy['security_recommendations'][0]}
- {strategy['security_recommendations'][1]}

## ⚠️ Known Failure Modes (To Avoid)
{strategy['known_failure_patterns']}

## 🛠️ Execution Strategy
{strategy['implementation_strategy']}
"""
        return doc, strategy
