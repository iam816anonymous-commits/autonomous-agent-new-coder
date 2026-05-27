import sqlite3
import json
import os

class DatasetExporter:
    def __init__(self, db_path):
        self.db_path = db_path

    def export_lora_jsonl(self, output_path):
        """Exports approved code snippets and repairs in JSONL format for LoRA fine-tuning."""
        print(f"📦 Exporting LoRA dataset to {output_path}...")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT file_path, content, tags FROM snippets WHERE status = "APPROVED" OR status = "MERGED"')
            rows = cursor.fetchall()

            with open(output_path, 'w') as f:
                for row in rows:
                    entry = {
                        "instruction": f"Write the code for {row[0]} following user style.",
                        "input": row[2],
                        "output": row[1]
                    }
                    f.write(json.dumps(entry) + "\n")

        return len(rows)
