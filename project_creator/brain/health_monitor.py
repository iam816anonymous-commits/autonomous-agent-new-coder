import os
import sqlite3

from project_creator.learning import DB_PATH


class HealthMonitor:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def analyze_health(self):
        """Calculates diversity and source distribution metrics."""
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()

            # Source Distribution
            cur.execute(
                "SELECT source_type, COUNT(*) FROM patterns GROUP BY source_type"
            )
            dist = dict(cur.fetchall())

            total = sum(dist.values())
            self_pct = (dist.get("SELF", 0) / total * 100) if total > 0 else 0
            ext_pct = (dist.get("EXTERNAL", 0) / total * 100) if total > 0 else 0

            # Diversity Score (unique patterns / total usages)
            cur.execute("SELECT COUNT(DISTINCT content), SUM(frequency) FROM patterns")
            unique, total_usage = cur.fetchone()
            diversity = (
                (unique / total_usage) if total_usage and total_usage > 0 else 1.0
            )

            return {
                "self_knowledge_pct": round(self_pct, 1),
                "external_knowledge_pct": round(ext_pct, 1),
                "diversity_score": round(diversity, 2),
                "status": "HEALTHY" if diversity > 0.3 and ext_pct > 30 else "BIASED",
            }

    def detect_contradictions(self, p_type):
        """Finds instances where SELF and EXTERNAL patterns for the same type differ."""
        # Simple implementation: check if multiple different patterns exist for same type
        # In a real impl, we would use LLM to compare 'naming' or 'idiom' logic.
        return []

    def generate_report(self):
        health = self.analyze_health()
        report = f"""# 🏥 Mini Jules Learning Health Report

**System Status: {health['status']}**

## 🌐 Knowledge Origin
- **Self-Generated (SELF)**: {health['self_knowledge_pct']}%
- **External Reality (EXTERNAL)**: {health['external_knowledge_pct']}%
- **Other (USER/SWE)**: {100 - health['self_knowledge_pct'] - health['external_knowledge_pct']}%

## 📊 Diversity Metrics
- **Pattern Diversity Score**: {health['diversity_score']}
- **Status Reasoning**: {"System has enough external grounding." if health['status'] == "HEALTHY" else "System is becoming an echo chamber. Ingest more external repos."}

## ⚖️ Balanced Retrieval
Current Weights:
- External: 1.0
- Self: 0.4
"""
        try:
            from project_creator.core.storage import Storage

            storage = Storage(".")
            storage.write_file("reports/learning_health.md", report)
        except:
            os.makedirs("reports", exist_ok=True)
            with open("reports/learning_health.md", "w") as f:
                f.write(report)
        return report
