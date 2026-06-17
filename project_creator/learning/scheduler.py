import datetime
import time

import psutil


class NightScheduler:
    def __init__(self, start_hour=0, end_hour=6, cpu_threshold=20, quota_threshold=100):
        self.start_hour = start_hour
        self.end_hour = end_hour
        self.cpu_threshold = cpu_threshold
        self.quota_threshold = quota_threshold
        self.is_running = False

    def is_window_active(self):
        now = datetime.datetime.now().hour
        if self.start_hour <= self.end_hour:
            return self.start_hour <= now < self.end_hour
        else:  # Window crosses midnight (e.g. 22 to 06)
            return now >= self.start_hour or now < self.end_hour

    def is_system_idle(self):
        # Check CPU usage
        cpu_usage = psutil.cpu_percent(interval=1)
        if cpu_usage > self.cpu_threshold:
            return False

        # Simulated user inactivity (could use pynput in real local environment)
        return True

    def check_quota(self):
        # Simulated quota check (1500 free requests per day for Gemini)
        # In a real impl, this would query a central service or local counter
        return 500 > self.quota_threshold

    def should_run(self):
        return self.is_window_active() and self.is_system_idle() and self.check_quota()

    def start_loop(self, task_callback):
        print(
            f"🌙 Night Scheduler: Monitoring window {self.start_hour:02d}:00 - {self.end_hour:02d}:00"
        )
        while True:
            if self.should_run():
                if not self.is_running:
                    print("🚀 Starting Night Learning session...")
                    self.is_running = True
                task_callback()
            else:
                if self.is_running:
                    print(
                        "🛑 Stopping Night Learning (window closed, system busy, or quota end)."
                    )
                    self.is_running = False
            time.sleep(60)  # Check every minute
