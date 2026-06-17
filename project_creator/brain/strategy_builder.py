class StrategyBuilder:
    def __init__(self, brain):
        self.brain = brain

    def generate_strategy_document(self, goal, context):
        """
        Builds the explicit Strategy Document required before generation.
        """
        doc = f"# 📑 Strategy Document: {goal}\n\n"

        # 1. Architecture Recommendation
        doc += "## 🏗️ Recommended Architecture\n"
        doc += f"{context.get('recommended_arch', 'Modular Monolith')}\n\n"

        # 2. Key Dependencies
        doc += "## 📦 Recommended Dependencies\n"
        doc += f"- {', '.join(context.get('recommended_deps', ['Python standard library']))}\n\n"

        # 3. Known Failure Patterns
        doc += "## ⚠️ Known Failure Patterns (Avoid)\n"
        failures = context.get("failure_patterns", [])
        if not failures:
            doc += "- No historical failures for this type.\n"
        else:
            for f in failures:
                doc += f"- {f}\n"
        doc += "\n"

        # 4. Successful Repair Strategies
        doc += "## 🛠️ Successful Repair Strategies (Reuse)\n"
        repairs = context.get("repair_strategies", [])
        if not repairs:
            doc += "- No relevant repair patterns found.\n"
        else:
            for r in repairs:
                doc += f"- {r}\n"
        doc += "\n"

        # 5. Security & Implementation Strategy
        doc += "## 🛡️ Security & Implementation Strategy\n"
        doc += "- Validate all user input (SQLi, XSS prevention)\n"
        doc += "- Use secure password hashing where applicable\n"
        doc += "- Implement health checks for critical modules\n"

        return doc
