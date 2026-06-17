import json
import os


class SWEBenchLoader:
    def __init__(self, local_data_path=None):
        self.data_path = local_data_path or os.path.join(
            "datasets", "swebench", "swe-bench.json"
        )

    def load_samples(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, "r") as f:
                return json.load(f)
        return []


class RepairExtractor:
    def extract_lessons(self, sample):
        """
        Extracts bug/repair knowledge from SWE-Bench samples.
        """
        return {
            "error": sample.get("problem_statement", "Unknown issue"),
            "root_cause": "Extracted from SWE-Bench historical record",
            "repair": sample.get("patch", "No patch available"),
            "repository": sample.get("repo", "unknown"),
        }
