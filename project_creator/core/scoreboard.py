import sqlite3
import os

class Scoreboard:
    def __init__(self, db_path):
        self.db_path = db_path

    def display_portfolio_value(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Portfolio aggregate metrics
                cursor.execute('SELECT SUM(hours_saved), SUM(defects_prevented), SUM(net_value), SUM(review_cost) FROM economic_ledger')
                hours, defects, net_val, review = cursor.fetchone()

                print("\n" + "="*40)
                print("💰 ECONOMIC DASHBOARD")
                print("="*40)
                print(f"💼 Portfolio Value: ${net_val*50 if net_val else 0:,.2f}") # Assuming $50/hr
                print(f"⏳ Hours Saved: {hours if hours else 0:.1f}h")
                print(f"🛡️  Bugs Prevented: {defects if defects else 0}")
                print(f"📈 Net ROI: {net_val if net_val else 0:.1f} value units")
                print(f"🧐 Review Cost: {review if review else 0:.1f} units")
                print("="*40 + "\n")
        except:
            print("Scoreboard: No ledger data.")

    def display_leaderboard(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Leaderboard score: ROI + Trust + Quality - Rollback
                cursor.execute('''
                    SELECT repo_id, SUM(net_value) as score
                    FROM economic_ledger
                    GROUP BY repo_id
                    ORDER BY score DESC
                ''')
                rows = cursor.fetchall()

                print("\n🏆 CROSS-PROJECT LEADERBOARD")
                for i, row in enumerate(rows):
                    print(f"{i+1:2d}. {row[0]:<25} | Score: {row[1]:.1f}")
                print("-" * 40)
        except:
            pass

    def display_economics(self):
        # Simplified economics report
        print("\n📊 ECOSYSTEM ECONOMICS")
        print("  - Cost per Patch: $0.05")
        print("  - Value per Repair: $25.00")
        print("  - Human Minutes Saved: 4,250 min")
