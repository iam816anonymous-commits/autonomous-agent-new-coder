import os
import shutil
import tempfile
from typing import Dict, Any, List
from project_creator.learning.event_bus import bus

class ValidationManager:
    """
    Handles the Sandbox Dry-run and Critique/Repair loop.
    """
    def __init__(self, agents, tools, repair_strategist=None):
        self.critique = agents['critique']
        self.repair = agents['repair']
        self.tools = tools
        self.repair_strategist = repair_strategist

    def run_dry_run(self, path: str, content: str, blueprint: Dict, generated_files: Dict, strategy_doc: str = None) -> Dict[str, Any]:
        """
        Executes a 3-attempt validation loop (Virtual Critique + Physical Lint).
        """
        current_content = content

        for attempt in range(3):
            print(f"🧪 [SANDBOX] Validating {path} (Attempt {attempt+1})")

            # 1. Virtual Critique
            audit = self.critique.analyze(path, current_content, blueprint, generated_files)

            # 2. Physical Validation
            physical_issues = self._lint_check(path, current_content)

            if audit.get('verdict') == "PASS" and not physical_issues:
                return {"path": path, "content": current_content, "status": "validated"}

            # Learning Events
            if audit.get('verdict') != "PASS":
                bus.publish("CRITIQUE_FAILED", {"path": path, "type": "CRITIQUE", "error": str(audit.get('issues')), "content": current_content})
            if physical_issues:
                bus.publish("VALIDATION_FAILED", {"path": path, "type": "SANDBOX", "error": str(physical_issues), "content": current_content})

            # 3. Repair
            combined = audit.get('issues', []) + physical_issues
            print(f"🛠️  Repairing {path} for: {combined}")

            if self.repair_strategist:
                patch = self.repair_strategist.formulate_repair(path, current_content, combined, blueprint, generated_files, extra_context=strategy_doc)
            else:
                patch = self.repair.propose_patch(path, current_content, combined, blueprint, generated_files, extra_context=strategy_doc)
            if patch and patch.get('new_content'):
                current_content = patch['new_content']
            else:
                break

        return {"path": path, "content": current_content, "status": "manual_review_needed"}

    def _lint_check(self, path: str, content: str) -> List[str]:
        issues = []
        sandbox_root = tempfile.mkdtemp(prefix="jules_vman_")
        try:
            sandbox_path = os.path.join(sandbox_root, path)
            os.makedirs(os.path.dirname(sandbox_path), exist_ok=True)
            with open(sandbox_path, "w") as f: f.write(content)

            orig_root = self.tools.project_root
            self.tools.project_root = sandbox_root
            lint_res = self.tools.run_lint(path)
            self.tools.project_root = orig_root

            if lint_res.get('returncode') != 0 and lint_res.get('stdout'):
                issues.append(f"Lint Fail: {lint_res['stdout']}")
        finally:
            shutil.rmtree(sandbox_root)
        return issues
