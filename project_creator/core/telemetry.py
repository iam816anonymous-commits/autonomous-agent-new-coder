import random
import time

class TelemetryEngine:
    def __init__(self, memory):
        self.memory = memory

    def capture_metrics(self, env, version):
        """Simulates capturing production/staging telemetry."""
        print(f"📊 Capturing telemetry for {env} [{version}]...")

        # Simulate data collection
        metrics = {
            'latency': random.uniform(100, 300), # ms
            'error_rate': random.choice([0, 0, 0, 0.01, 0.05]), # %
            'cost': random.uniform(0.1, 2.0), # $
            'usage': random.randint(1000, 5000) # reqs
        }

        for metric, value in metrics.items():
            self.memory.log_telemetry(env, version, metric, value)

        return metrics

    def check_health(self, env, version):
        """Checks if current telemetry is within acceptable bounds."""
        error_rate = self.memory.get_latest_telemetry(env, 'error_rate')
        if error_rate is not None and error_rate > 0.02:
            return False, f"High error rate: {error_rate*100}%"
        return True, "Healthy"
