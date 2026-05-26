import time
import json

class CompareEngine:
    @staticmethod
    def compare(current_metrics, candidate_metrics):
        """Compares two sets of metrics and returns a win/loss/draw report."""
        comparison = {
            "latency": candidate_metrics.get('latency', 0) - current_metrics.get('latency', 0),
            "tests": candidate_metrics.get('tests_passed', 0) - current_metrics.get('tests_passed', 0),
            "cost": candidate_metrics.get('cost', 0) - current_metrics.get('cost', 0),
            "winner": "current",
            "reasons": []
        }

        # Win conditions
        if candidate_metrics.get('latency', 0) < current_metrics.get('latency', 0) * 0.95:
            comparison['reasons'].append("Significant latency improvement (>5%)")
            comparison['winner'] = "candidate"

        if candidate_metrics.get('tests_passed', 0) > current_metrics.get('tests_passed', 0):
             comparison['reasons'].append("Increased test coverage/passing")
             comparison['winner'] = "candidate"

        if candidate_metrics.get('cost', 0) > current_metrics.get('cost', 0) * 1.2:
             comparison['reasons'].append("Significant cost increase (>20%)")
             comparison['winner'] = "current"

        return comparison

class ShadowExecutor:
    def __init__(self, current_agent, candidate_agent, tools):
        self.current_agent = current_agent
        self.candidate_agent = candidate_agent
        self.tools = tools

    def run_shadow_workload(self, task, context):
        """Runs the same task on both current and candidate agents and compares performance."""
        print(f"🕵️  Shadow Execution: Running task '{task}'...")

        # Current Agent Run
        start = time.time()
        res_current = self.current_agent.generate_code("shadow_file.py", task, {}, context)
        latency_current = time.time() - start

        # Candidate Agent Run (Simulated as a slightly different prompt or updated logic)
        start = time.time()
        res_candidate = self.candidate_agent.generate_code("shadow_file.py", task, {}, context)
        latency_candidate = time.time() - start

        return {
            "current": {"latency": latency_current, "content": res_current},
            "candidate": {"latency": latency_candidate, "content": res_candidate}
        }
