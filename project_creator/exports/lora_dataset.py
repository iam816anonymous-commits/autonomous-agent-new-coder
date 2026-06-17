import json
import sqlite3


class DatasetExporter:
    def __init__(self, db_path):
        self.db_path = db_path

    def export_lora_jsonl(self, output_path):
        """Exports successful solve->repair chains for LoRA fine-tuning."""
        print(f"📦 Exporting Night Learning dataset to {output_path}...")

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Export snippet solving chains
            cursor.execute(
                'SELECT file_path, content, tags FROM snippets WHERE status = "APPROVED" OR status = "ACCEPTED"'
            )
            rows = cursor.fetchall()

            count = 0
            with open(output_path, "w") as f:
                for row in rows:
                    # P3-12: Use actual task metadata for instruction if available
                    instruction = f"Solve a coding task for {row['file_path']}."
                    if row["tags"]:
                        try:
                            tags = json.loads(row["tags"])
                            if "instruction" in tags:
                                instruction = tags["instruction"]
                        except:
                            pass

                    entry = {
                        "instruction": instruction,
                        "output": row["content"],
                        "metadata": {
                            "file_path": row["file_path"],
                            "tags": row["tags"],
                        },
                    }
                    f.write(json.dumps(entry) + "\n")
                    count += 1

        return count
