import sqlite3

from project_creator.learning import DB_PATH


class IntelligenceScore:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def calculate_score(self):
        """
        Calculates the 0-100 Intelligence Score based on actual DB metrics.
        Weights:
        0.30 * Repair Success (from failures vs repairs)
        0.25 * Knowledge Density (from patterns learned)
        0.20 * Retrieval Diversity (from source types)
        0.15 * Activity Level (from snippets added)
        0.10 * Completion Rate (from manifest statuses)
        """
        metrics = {
            "repair_success": 0,
            "knowledge_density": 0,
            "retrieval_diversity": 0,
            "activity_level": 0,
            "completion_rate": 0,
        }

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 1. Repair Success
                cursor.execute("SELECT COUNT(*) FROM failures")
                fail_count = cursor.fetchone()[0]
                cursor.execute(
                    "SELECT COUNT(*) FROM snippets WHERE status = 'REPAIRED'"
                )
                repair_count = cursor.fetchone()[0]
                metrics["repair_success"] = (
                    min(1.0, repair_count / fail_count) if fail_count > 0 else 0.5
                )

                # 2. Knowledge Density
                cursor.execute("SELECT COUNT(*) FROM patterns")
                pattern_count = cursor.fetchone()[0]
                metrics["knowledge_density"] = min(
                    1.0, pattern_count / 100
                )  # Target 100 patterns

                # 3. Retrieval Diversity
                cursor.execute("SELECT COUNT(DISTINCT source_type) FROM patterns")
                source_count = cursor.fetchone()[0]
                metrics["retrieval_diversity"] = min(
                    1.0, source_count / 4
                )  # SELF, EXTERNAL, SWE_BENCH, USER

                # 4. Activity Level
                cursor.execute("SELECT COUNT(*) FROM snippets")
                snippet_count = cursor.fetchone()[0]
                metrics["activity_level"] = min(
                    1.0, snippet_count / 50
                )  # Target 50 snippets

                # 5. Completion Rate (Heuristic from approved snippets vs total attempted)
                cursor.execute(
                    "SELECT COUNT(*) FROM snippets WHERE status = 'APPROVED' OR status = 'ACCEPTED'"
                )
                success_count = cursor.fetchone()[0]
                metrics["completion_rate"] = (
                    min(1.0, success_count / snippet_count)
                    if snippet_count > 0
                    else 0.5
                )

        except Exception as e:
            print(f"⚠️  IntelligenceScore: Failed to query real metrics: {e}")

        score = (
            0.30 * metrics["repair_success"]
            + 0.25 * metrics["knowledge_density"]
            + 0.20 * metrics["retrieval_diversity"]
            + 0.15 * metrics["activity_level"]
            + 0.10 * metrics["completion_rate"]
        )

        return round(score * 100, 1), metrics

    def generate_report(self):
        score, metrics = self.calculate_score()
        report = f"""# 🧠 Mini Jules Brain Report

**Intelligence Score: {score}/100**

## 📊 Performance Metrics
- **Repair Success**: {metrics['repair_success']*100:.1f}%
- **Knowledge Density**: {metrics['knowledge_density']*100:.1f}%
- **Retrieval Diversity**: {metrics['retrieval_diversity']*100:.1f}%
- **Activity Level**: {metrics['activity_level']*100:.1f}%
- **Completion Rate**: {metrics['completion_rate']*100:.1f}%

## 📚 Knowledge Stats
- **Patterns Learned**: (Queried from SQL)
- **Repairs Stored**: (Queried from Vector Store)
- **Repositories Indexed**: (Queried from Brain Indexer)
"""
        try:
            from project_creator.core.storage import Storage

            storage = Storage(".")
            storage.write_file("reports/brain_report.md", report)
        except:
            with open("reports/brain_report.md", "w") as f:
                f.write(report)
        print("✅ Brain: Intelligence Report generated at reports/brain_report.md")
        return report
