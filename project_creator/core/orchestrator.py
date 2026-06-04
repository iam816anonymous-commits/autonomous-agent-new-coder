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
from project_creator.core.validation import ValidationManager
from project_creator.core.repair_strategist import RepairStrategist
from project_creator.core.generation_coordinator import GenerationCoordinator
from project_creator.core.execution_coordinator import ExecutionCoordinator

class Orchestrator:
    def __init__(self, router, agents, storage, tools, manifest, session):
        self.router = router
        self.planner = agents['planner']
        self.coder = agents['coder']

        # Core Components
        self.error_classifier = ErrorClassifier()
        self.test_executor = TestExecutor(storage.project_root)
        self.repair_strategist = RepairStrategist(agents['repair'], self.error_classifier, storage.project_root)
        self.validation_manager = ValidationManager(agents, tools, self.repair_strategist)
        self.gen_coordinator = GenerationCoordinator(self.coder, self.validation_manager)
        self.exec_coordinator = ExecutionCoordinator(tools, self.test_executor)

        # Specialist Agents
        self.dialogue = DialogueAgent(router)
        self.dependency_analyzer = DependencyAnalyzer()

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
        print("🧪 Starting Verified Sandbox Test-Repair Cycle...")
        strategy_doc = getattr(self, 'strategy_doc', None)

        for cycle in range(max_repair_cycles):
            res = self.test_executor.run_tests()
            if res.get('returncode') == 0:
                print("✅ All tests passed!")
                return True

            context = self.test_executor.generate_repair_context(res)
            print(f"❌ Test Failed (Cycle {cycle+1}). Type: {context['failure_type']}")

            # Formulate repair for the project based on test failure
            repair_tasks = self.repair_strategist.formulate_repair(
                "PROJECT_TESTS",
                "", # No single file content, repairing project
                [f"Test Failure: {context['stderr']}"],
                self.blueprint,
                self.generated_files,
                extra_context=strategy_doc
            )

            if repair_tasks and repair_tasks.get('new_content'):
                # In a real multi-file repair, the strategist might return multiple patches.
                # Here we assume it targets a specific file identified in the repair task.
                target_path = repair_tasks.get('path')
                if target_path:
                    print(f"🛠️  Applying repair to {target_path}...")
                    self.apply(target_path, repair_tasks['new_content'])
                else:
                    print("⚠️  Repair proposed but no target file specified.")
                    break
            else:
                print("⚠️  No repair plan could be formulated.")
                break

        return False

    def plan(self, goal: str):
        # 0. Brain Consultation & Strategy Document
        brain = EngineeringBrain(DB_PATH)
        self.strategy_doc, strategy_data = brain.consult(goal)
        print(f"\n🧠 BRAIN STRATEGY:\n{self.strategy_doc}\n")

        print(f"🏗️  Architecting: {goal}")
        self.blueprint = self.planner.create_blueprint(goal, strategy_doc=self.strategy_doc)
        if self.blueprint:
             # Flatten files for manifest compatibility
             all_files = []
             for stage in self.blueprint.get('stages', []):
                 all_files.extend([f['path'] for f in stage['files']])

             self.manifest.create(goal, "python-sandbox", all_files)
             self.session.save_session(self.blueprint, {}, [], [])
             # Learning Event
             collector.collect("PLAN_CREATED", {"goal": goal, "files": all_files})
        return self.blueprint

    def generate_and_validate(self, file_meta: Dict[str, str]):
        strategy_doc = getattr(self, 'strategy_doc', None)
        return self.gen_coordinator.generate_project_file(file_meta, self.blueprint, self.generated_files, strategy_doc=strategy_doc)

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
