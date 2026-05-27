import sqlite3
import json
import os

class DatasetExporter:
    def __init__(self, db_path):
        self.db_path = db_path

    def export_lora_jsonl(self, output_path):
        """Exports successful solve->repair chains for LoRA fine-tuning."""
        print(f"📦 Exporting Night Learning dataset to {output_path}...")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Export snippet solving chains
            cursor.execute('SELECT file_path, content FROM snippets WHERE status = "APPROVED"')
            rows = cursor.fetchall()

            count = 0
            with open(output_path, 'w') as f:
                for row in rows:
                    entry = {
                        "instruction": f"Solve a coding task for {row[0]}.",
                        "output": row[1]
                    }
                    f.write(json.dumps(entry) + "\n")
                    count += 1

        return count
