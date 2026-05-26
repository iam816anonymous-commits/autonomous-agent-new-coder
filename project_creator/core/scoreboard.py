import sqlite3
import os

class Scoreboard:
    def __init__(self, db_path):
        self.db_path = db_path

    def get_summary(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Global Trends
                cursor.execute('SELECT avg_quality_score, promotion_rate, rollback_rate, drift_rate FROM ecosystem_metrics ORDER BY timestamp DESC LIMIT 1')
                row = cursor.fetchone()

                # Version Counts
                cursor.execute('SELECT COUNT(*) FROM versions')
                total_versions = cursor.fetchone()[0]

                # Champion info
                cursor.execute('SELECT version_tag FROM versions WHERE is_champion = 1')
                champion = cursor.fetchone()

                return {
                    "quality": row[0] if row else 0,
                    "promotion_rate": row[1] if row else 0,
                    "rollback_rate": row[2] if row else 0,
                    "drift_rate": row[3] if row else 0,
                    "total_versions": total_versions,
                    "current_champion": champion[0] if champion else "None"
                }
        except:
            return None

    def display(self):
        s = self.get_summary()
        if not s:
            print("\n📊 Scoreboard: No data available yet.")
            return

        print("\n" + "="*40)
        print("📊 ECOSYSTEM SCOREBOARD")
        print("="*40)
        print(f"🏆 Champion: {s['current_champion']}")
        print(f"📂 Total Versions: {s['total_versions']}")
        print(f"📈 Quality Score: {s['quality']:.1f}%")
        print(f"🚀 Promotion Rate: {s['promotion_rate']*100:.1f}%")
        print(f"🚨 Rollback Rate: {s['rollback_rate']*100:.1f}%")
        print(f"📉 Drift Rate: {s['drift_rate']*100:.1f}%")
        print("="*40 + "\n")
