class EconomicScorer:
    @staticmethod
    def calculate_score(metrics):
        """
        score = quality + latency_gain + trust - cost - rollback_risk
        """
        quality = metrics.get('quality', 0) * 0.4
        latency_gain = metrics.get('latency_gain', 0) * 0.2
        trust = metrics.get('trust_score', 0) * 0.2
        cost = metrics.get('cost', 0) * 0.1
        risk = metrics.get('rollback_risk', 0) * 0.1

        score = quality + latency_gain + trust - cost - risk
        return round(score, 2)

    @staticmethod
    def should_promote(candidate_score, champion_score):
        # Promotion becomes economic: only promote if score is higher
        return candidate_score > champion_score
