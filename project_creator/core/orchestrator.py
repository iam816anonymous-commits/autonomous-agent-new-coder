import os
import json
import shutil
import tempfile
from typing import Dict, Any, List
from project_creator.learning.collector import collector
from project_creator.brain.engineering_brain import EngineeringBrain
from project_creator.learning import DB_PATH
from project_creator.agents.dialogue_agent import DialogueAgent
from project_creator.brain.dependency_analyzer import DependencyAnalyzer
from project_creator.core.test_executor import TestExecutor
from project_creator.core.error_classifier import ErrorClassifier

class Orchestrator:
    def __init__(self, router, agents, storage, tools, manifest, session):
        self.router = router
        self.planner = agents['planner']
        self.coder = agents['coder']
        self.critique = agents['critique']
        self.repair = agents['repair']

        # New Agents
        self.dialogue = DialogueAgent(router)
        self.dependency_analyzer = DependencyAnalyzer()
        self.test_executor = TestExecutor(storage.project_root)
        self.error_classifier = ErrorClassifier()

        self.storage = storage
        self.tools = tools
        self.manifest = manifest
        self.session = session

        self.blueprint = None
        self.generated_files = {}

    def gather_requirements(self, goal):
        return self.dialogue.gather_requirements(goal)

    def validate_architecture_with_user(self, architecture):
        print("\n🔍 Validating Architecture...")
        verdict = self.dialogue.validate_architecture(architecture)
        print(f"Brain Verdict: {verdict}")
        return verdict

    def generate_with_dependency_order(self):
        if not self.blueprint: return
        self.dependency_analyzer.analyze_project(self.blueprint['files'])
        order = self.dependency_analyzer.get_dependency_order()

        print(f"📊 Generation Order: {' -> '.join(order)}")

        # Mapping path back to file metadata
        meta_map = {f['path']: f for f in self.blueprint['files']}

        for path in order:
            if path in meta_map:
                res = self.generate_and_validate(meta_map[path])
                self.apply(path, res['content'])

    def validate_dependencies(self):
        print("🔗 Validating inter-file dependencies...")
        return self.dependency_analyzer.analyze_project(self.blueprint['files'] if self.blueprint else [])

    def run_tests_with_repair(self, max_repair_cycles=3):
        print("🧪 Starting Test-Driven Repair Cycle...")
        for cycle in range(max_repair_cycles):
            res = self.test_executor.run_tests()
            if res.get('returncode') == 0:
                print("✅ All tests passed!")
                return True

            context = self.test_executor.generate_repair_context(res)
            cat, sev = self.error_classifier.classify_error(context['stderr'])
            plan = self.error_classifier.get_repair_plan(cat)

            print(f"❌ Test Failed (Cycle {cycle+1}). Category: {cat.value}, Severity: {sev.name}")
            print(f"💡 Repair Plan: {plan}")

            # Real repair would loop through files and patch
        return False

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
            self.session.save_session(self.blueprint, self.generated_files, [], [p for p in self.generated_files.keys()])
            # Learning Event
            collector.collect("PATCH_ACCEPTED", {"path": path, "content": content})
            return True
        return False

    def finalize(self):
        """Triggers self-learning after project completion."""
        print("🏁 Project finalized. Triggering Brain Self-Learning...")
        brain = EngineeringBrain(DB_PATH)
        session_data = self.session.load_session()
        if session_data:
            brain.learn_from_completed_task(session_data)
