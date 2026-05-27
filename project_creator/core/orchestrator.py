import os
import json
from typing import Dict, Any, List

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
        print(f"🏗️  Architecting Goal: {goal}")
        self.blueprint = self.planner.create_blueprint(goal)
        if self.blueprint:
             self.manifest.create(goal, "python-hardened", [f['path'] for f in self.blueprint['files']])
             self.session.save_session(self.blueprint, {}, [], [])
        return self.blueprint

    def generate_and_validate(self, file_meta: Dict[str, str]):
        path = file_meta['path']
        print(f"📝 Processing: {path}")

        # 1. Generate
        content = self.coder.generate_file(path, file_meta['description'], self.blueprint, self.generated_files)

        # 2. Iterative SDLC with real tool feedback
        for attempt in range(3):
            # 3. Virtual Audit (LLM)
            audit = self.critique.analyze(path, content, self.blueprint, self.generated_files)

            # 4. Physical Audit (Tools - simulated by writing to temp or sandbox)
            tool_errors = []
            if path.endswith(".py"):
                # We simulate tool run by checking syntax at least
                try:
                    compile(content, path, 'exec')
                except Exception as e:
                    tool_errors.append(f"Syntax Error: {e}")

            if audit.get('verdict') == "PASS" and not tool_errors:
                return {"path": path, "content": content, "status": "validated", "audit": audit}

            # 5. Combined Repair
            combined_issues = audit.get('issues', []) + tool_errors
            print(f"🛠️  Repair attempt {attempt+1} for {path}. Issues: {combined_issues}")

            patch = self.repair.propose_patch(path, content, combined_issues, self.blueprint, self.generated_files)
            if patch and patch.get('new_content'):
                content = patch['new_content']
            else:
                break

        return {"path": path, "content": content, "status": "failed_validation", "issues": combined_issues}

    def apply(self, path: str, content: str):
        if self.storage.write_file(path, content, interactive=False):
            self.generated_files[path] = content
            self.manifest.add_approval(path)
            self.session.save_session(self.blueprint, self.generated_files, [], [p for p in self.generated_files])
            return True
        return False
