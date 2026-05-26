import time
import json

class DriftDetector:
    @staticmethod
    def detect(current_metrics, candidate_metrics):
        if candidate_metrics.get('latency', 0) > current_metrics.get('latency', 0) * 1.1:
            return True, "Latency drift detected"
        if candidate_metrics.get('tests_passed', 0) < current_metrics.get('tests_passed', 0):
             return True, "Quality drift detected"
        return False, "Stable"

    @staticmethod
    def should_retire_champion(champ_metrics, recent_telemetry):
        """Checks if current champion has drifted beyond acceptable thresholds."""
        avg_latency = recent_telemetry.get('latency', 0)
        if avg_latency > champ_metrics.get('latency', 0) * 1.5:
            return True, "Champion retired: Persistent latency drift (>50%)"
        error_rate = recent_telemetry.get('error_rate', 0)
        if error_rate > 0.05:
            return True, "Champion retired: High production error rate (>5%)"
        return False, "Champion stable"

class CompareEngine:
    @staticmethod
    def generate_scorecard(candidate_id, current_metrics, candidate_metrics):
        return {
            "candidate": candidate_id,
            "latency_delta": candidate_metrics.get('latency', 0) - current_metrics.get('latency', 0),
            "cost_delta": candidate_metrics.get('cost', 0) - current_metrics.get('cost', 0),
            "tests_delta": candidate_metrics.get('tests_passed', 0) - current_metrics.get('tests_passed', 0),
            "approval_rate": candidate_metrics.get('approval_rate', 0),
            "repair_success": candidate_metrics.get('repair_success', 0),
            "promotion": "rejected"
        }

class ShadowExecutor:
    def __init__(self, current_agent, tools):
        self.current_agent = current_agent
        self.tools = tools

    def run_shadow_workload(self, task, context, challenger_agents):
        print(f"🕵️  Shadow Execution: Champion vs {len(challenger_agents)} Challengers...")
        start = time.time()
        res_champ = self.current_agent.generate_code("shadow_file.py", task, {}, context)
        latency_champ = time.time() - start

        results = {"champion": {"latency": latency_champ, "content": res_champ}}
        for i, agent in enumerate(challenger_agents):
            start = time.time()
            res_chal = agent.generate_code("shadow_file.py", task, {}, context)
            results[f"challenger_{i}"] = {"latency": time.time() - start, "content": res_chal}
        return results
