import os
import json
import shutil
import tempfile
from typing import Dict, Any, List
from project_creator.learning.collector import collector
from project_creator.brain.engineering_brain import EngineeringBrain
from project_creator.learning import DB_PATH

class Orchestrator:
    def __init__(self, router, agents, storage, tools, manifest, session):
        self.router = router
        self.planner = agents['planner']
        self.coder = agents['coder']
        self.critique = agents['critique']
        self.repair = agents['repair']
        self.storage = storage
        self.tools = tools
        self.manifest = manifest
        self.session = session

        self.blueprint = None
        self.generated_files = {}

    def plan(self, goal: str):
        # 0. Brain Consultation & Strategy Document
        brain = EngineeringBrain(DB_PATH)
        strategy_doc, strategy_data = brain.consult(goal)
        print(f"\n🧠 BRAIN STRATEGY:\n{strategy_doc}\n")

        print(f"🏗️  Architecting: {goal}")
        self.blueprint = self.planner.create_blueprint(goal)
        if self.blueprint:
             self.manifest.create(goal, "python-sandbox", [f['path'] for f in self.blueprint['files']])
             self.session.save_session(self.blueprint, {}, [], [])
             # Learning Event
             collector.collect("PLAN_CREATED", {"goal": goal, "files": [f['path'] for f in self.blueprint['files']]})
        return self.blueprint

    def generate_and_validate(self, file_meta: Dict[str, str]):
        path = file_meta['path']
        print(f"📝 Generating: {path}")

        content = self.coder.generate_file(path, file_meta['description'], self.blueprint, self.generated_files)

        # Sandbox Dry-run Loop
        for attempt in range(3):
            print(f"🧪 [SANDBOX] Validating {path} (Attempt {attempt+1})")

            # 1. Virtual Critique
            audit = self.critique.analyze(path, content, self.blueprint, self.generated_files)

            # 2. Physical Validation (Syntax & Lint)
            sandbox_root = tempfile.mkdtemp(prefix="jules_sandbox_")
            try:
                sandbox_path = os.path.join(sandbox_root, path)
                os.makedirs(os.path.dirname(sandbox_path), exist_ok=True)
                with open(sandbox_path, "w") as f: f.write(content)

                orig_root = self.tools.project_root
                self.tools.project_root = sandbox_root
                lint_res = self.tools.run_lint(path)
                self.tools.project_root = orig_root

                physical_issues = []
                if lint_res.get('returncode') != 0 and lint_res.get('stdout'):
                    physical_issues.append(f"Lint Fail: {lint_res['stdout']}")

                if audit.get('verdict') == "PASS" and not physical_issues:
                    return {"path": path, "content": content, "status": "validated"}

                # Learning Event: Validation Failure
                from project_creator.learning.event_bus import bus
                if audit.get('verdict') != "PASS":
                    bus.publish("CRITIQUE_FAILED", {"path": path, "type": "CRITIQUE", "error": str(audit.get('issues')), "content": content})
                if physical_issues:
                    bus.publish("VALIDATION_FAILED", {"path": path, "type": "SANDBOX", "error": str(physical_issues), "content": content})

                # 3. Repair with combined virtual/physical feedback
                combined = audit.get('issues', []) + physical_issues

                # Enhance repair with semantic historical context
                from project_creator.memory.retriever import Retriever
                from project_creator.learning import DB_PATH
                retriever = Retriever(DB_PATH)
                semantic_history = retriever.augment_prompt(f"Fix issues in {path}: {combined}", task_type="repair", path=path)

                print(f"🛠️  Repairing {path} for: {combined}")
                patch = self.repair.propose_patch(path, content, combined, self.blueprint, self.generated_files, extra_context=semantic_history)
                if patch and patch.get('new_content'):
                    content = patch['new_content']
                    # Learning Event
                    collector.collect("REPAIR", {"path": path, "issues": combined})
                else: break
            finally:
                shutil.rmtree(sandbox_root)

        return {"path": path, "content": content, "status": "manual_review_needed"}

    def apply(self, path: str, content: str):
        if self.storage.write_file(path, content, interactive=False):
            self.generated_files[path] = content
            self.manifest.add_approval(path)
            self.session.save_session(self.blueprint, self.generated_files, [], [p for p in self.generated_files])
            # Learning Event
            collector.collect("PATCH_ACCEPTED", {"path": path, "content": content})
            return True
        return False
