import os
import json

class SWEBenchLoader:
    def __init__(self, local_path=None):
        self.local_path = local_path or os.path.join("datasets", "swebench", "data.json")

    def load_data(self):
        if os.path.exists(self.local_path):
            print(f"📁 Loading local SWE-Bench data from {self.local_path}")
            with open(self.local_path, 'r') as f:
                return json.load(f)
        else:
            print("🌐 Falling back to remote SWE-Bench (Simulated)")
            # In real impl, use datasets library: load_dataset("princeton-nlp/SWE-bench")
            return []

class RepairExtractor:
    def extract_lessons(self, item):
        """Extracts bug/repair pairs from SWE-Bench items."""
        return {
            "bug": item.get("problem_statement"),
            "repository": item.get("repo"),
            "patch": item.get("patch"),
            "repair_strategy": "Extracted from SWE-Bench patch"
        }
