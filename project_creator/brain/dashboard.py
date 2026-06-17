from .intelligence_score import IntelligenceScore


class IntelligenceDashboard:
    def __init__(self, db_path):
        self.scorer = IntelligenceScore(db_path)

    def display_stats(self):
        score, metrics = self.scorer.calculate_score()
        print("\n" + "=" * 50)
        print("🤖 MINI JULES INTELLIGENCE DASHBOARD")
        print("=" * 50)
        print(f"OVERALL SCORE: {score}/100")
        print("-" * 50)
        print(f"Repair Reuse:    {metrics['repair_success']*100}%")
        print(f"Arch Reuse:      {metrics['arch_quality']*100}%")
        print(f"Pattern Reuse:   {metrics['pattern_reuse']*100}%")
        print("-" * 50)
        print("Memory: [SQL + VECTOR INDEXED]")
        print("=" * 50 + "\n")

    def export_report(self):
        return self.scorer.generate_report()
