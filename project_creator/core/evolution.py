import time
import json

class DriftDetector:
    @staticmethod
    def detect(current_metrics, candidate_metrics):
        """Detects if a candidate shows significant negative drift."""
        # Reject if latency increases by > 10%
        if candidate_metrics.get('latency', 0) > current_metrics.get('latency', 0) * 1.1:
            return True, "Latency drift detected (>10% regression)"
        # Reject if cost increases significantly
        if candidate_metrics.get('cost', 0) > current_metrics.get('cost', 0) * 1.5:
             return True, "Cost drift detected (>50% regression)"
        # Reject if tests passed decreases
        if candidate_metrics.get('tests_passed', 0) < current_metrics.get('tests_passed', 0):
             return True, "Quality drift detected (test regression)"
        return False, "No significant drift"

class CompareEngine:
    @staticmethod
    def generate_scorecard(candidate_id, current_metrics, candidate_metrics):
        """Generates an evidence-based scorecard comparing a candidate to the champion."""
        return {
            "candidate": candidate_id,
            "latency_delta": candidate_metrics.get('latency', 0) - current_metrics.get('latency', 0),
            "cost_delta": candidate_metrics.get('cost', 0) - current_metrics.get('cost', 0),
            "tests_delta": candidate_metrics.get('tests_passed', 0) - current_metrics.get('tests_passed', 0),
            "approval_rate": candidate_metrics.get('approval_rate', 0),
            "repair_success": candidate_metrics.get('repair_success', 0),
            "promotion": "rejected" # Default
        }

class ShadowExecutor:
    def __init__(self, current_agent, tools):
        self.current_agent = current_agent
        self.tools = tools

    def run_shadow_workload(self, task, context, challenger_agents):
        """Runs the same task on champion and multiple challenger agents."""
        print(f"🕵️  Shadow Execution: Champion vs {len(challenger_agents)} Challengers...")

        # Champion Run
        start = time.time()
        res_champ = self.current_agent.generate_code("shadow_file.py", task, {}, context)
        latency_champ = time.time() - start

        results = {
            "champion": {"latency": latency_champ, "content": res_champ}
        }

        # Challenger Runs
        for i, agent in enumerate(challenger_agents):
            start = time.time()
            res_chal = agent.generate_code("shadow_file.py", task, {}, context)
            latency_chal = time.time() - start
            results[f"challenger_{i}"] = {"latency": latency_chal, "content": res_chal}

        return results
