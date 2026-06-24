import json

from project_creator.learning.task_generator import TaskGenerator


class SelfPlayEngine:
    def __init__(self, router, agents, memory):
        self.router = router
        self.agents = agents  # coder, critique, repair
        self.memory = memory
        self.generator = TaskGenerator(router)

    def run_cycle(self):
        print("🏁 Self-Play: Generating task...")
        task = self.generator.generate_task()
        if not task:
            return

        print(f"🧠 Task: {task['problem']} [{task['difficulty']}]")

        # 1. Solve
        content = self.agents["coder"].generate_file(
            "self_play.py", task["problem"], {}, {}
        )

        # 2. Critique
        audit = self.agents["critique"].analyze("self_play.py", content, {}, {})

        # 3. Repair (Iterative)
        repair_chain = []
        if audit.get("verdict") == "FAIL":
            print("🛠️  Self-Play: Repair needed...")
            patch = self.agents["repair"].propose_patch(
                "self_play.py", content, audit["issues"], {}, {}
            )
            if patch and patch.get("new_content"):
                repair_chain.append(
                    {"issue": audit["issues"], "patch": patch["reason"]}
                )
                content = patch["new_content"]
                # Final verify
                audit = self.agents["critique"].analyze("self_play.py", content, {}, {})

        # 4. Benchmark & Quality Filter
        if audit.get("verdict") == "PASS":
            print("✅ Self-Play: Task Solved Successfully. Reflecting...")
            heuristic = self._reflect(task, content)
            self._store_learning(task, content, repair_chain, heuristic)
        else:
            print("❌ Self-Play: Failed to solve task. Discarding.")

    def _reflect(self, task, solution):
        prompt = f"Topic: {task['topic']}\nSolution:\n{solution}\nSummarize one core coding heuristic or 'best practice' derived from this solution in one sentence."
        try:
            return self.router.generate(prompt, "You are a senior mentor.")
        except:
            return None

    def _store_learning(self, task, solution, repair_chain, heuristic=None):
        # Store patterns and successful solve->repair chains
        # P3-12: Preserve actual task metadata in tags for better LoRA export quality
        tags = json.dumps(
            {
                "task_id": task["id"],
                "topic": task["topic"],
                "difficulty": task["difficulty"],
                "repair_chain": repair_chain,
                "instruction": task["problem"],
            }
        )
        self.memory.add_snippet(
            "self_play", solution, "APPROVED", source_type="SELF", tags=tags
        )
        # Update snippet with tags (assumes add_snippet logic might need to be extended or we use a separate call)
        # For now, we'll ensure add_snippet is used correctly.
        # CodingMemory.add_snippet currently signature: add_snippet(self, path, content, status, source_type="SELF")
        # Snippets table has a 'tags' column, but add_snippet doesn't expose it.

        if heuristic:
            self.memory.add_heuristic(task["topic"], heuristic)

        print(f"💾 Stored learning and heuristic for task {task['id']}")
