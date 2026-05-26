class EconomicScorer:
    @staticmethod
    def calculate_champion_score(metrics):
        """
        champion_score = quality_gain + trust_gain + roi - rollback_risk - cost
        """
        # Multipliers represent business value importance
        quality_gain = metrics.get('quality_gain', 0) * 0.3
        trust_gain = metrics.get('trust_gain', 0) * 0.3
        roi = metrics.get('roi_hours', 0) * 0.2
        risk = metrics.get('rollback_risk', 0) * 0.1
        cost = metrics.get('cost', 0) * 0.1

        score = quality_gain + trust_gain + roi - risk - cost
        return round(score, 2)

    @staticmethod
    def should_promote(candidate_score, champion_score):
        # Promotion is purely value-driven: higher score wins.
        return candidate_score > champion_score
