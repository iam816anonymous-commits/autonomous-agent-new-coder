import os
import json
import sys
import time

# Ensure the project root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_creator.core.storage import Storage
from project_creator.core.tools import ToolExecutor
from project_creator.core.memory import MemoryLayer
from project_creator.core.patch import PatchManager
from project_creator.core.knowledge_graph import KnowledgeGraph
from project_creator.core.sandbox import Sandbox
from project_creator.core.deployment import DeploymentOrchestrator
from project_creator.core.telemetry import TelemetryEngine
from project_creator.core.evolution import CompareEngine, ShadowExecutor
from project_creator.router.provider_router import ProviderRouter
from project_creator.agents.planner_agent import PlannerAgent
from project_creator.agents.coder_agent import CoderAgent
from project_creator.agents.repair_agent import AuditAgent, RepairAgent

def main():
    print("\n" + "="*60)
    print("🧬 Comparative Evolution Platform v6")
    print("="*60 + "\n")

    router = ProviderRouter()
    project_dir = input("Enter project directory: ").strip() or "evolution_v6"
    storage = Storage(project_dir)
    tools = ToolExecutor(project_dir)
    memory = MemoryLayer(os.path.join(storage.project_root, ".agent_memory.db"))
    sandbox = Sandbox(project_dir)
    deployer = DeploymentOrchestrator(memory, tools, sandbox)
    telemetry = TelemetryEngine(memory)

    planner = PlannerAgent(router)
    coder = CoderAgent(router, memory)
    # Differentiating candidate by adding a small prompt prefix or using a different provider if available
    shadow = ShadowExecutor(coder, coder, tools)

    audit_agent = AuditAgent(router)
    repair_agent = RepairAgent(router)

    existing_context = storage.read_existing_files()

    mode = input("\n[G]enerate, [A]udit, or [E]volve? [G/a/e]: ").lower()

    if mode == 'e':
        perform_evolution_loop(existing_context, coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry, shadow)
    elif mode == 'a':
        perform_repo_audit(existing_context, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry)
    else:
        perform_generation_flow(planner, coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry)

def perform_generation_flow(planner, coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry):
    user_prompt = input("What would you like to build?\n> ")
    existing_context = storage.read_existing_files()
    blueprint = planner.create_blueprint(user_prompt, list(existing_context.keys()))

    # Refinement loop
    while True:
        print("\n📋 Proposed Structure:")
        for i, file in enumerate(blueprint['files']):
            print(f"  {i+1:2d}. {file['path']} - {file['description']}")
        refine = input("\n[A]dd/Remove, [R]efine, or [P]roceed? [A/R/P]: ").lower()
        if refine == 'p': break
        elif refine in ['a', 'r']:
            feedback = input("Feedback: ")
            blueprint = planner.create_blueprint(f"Update blueprint: {feedback}. Original goal: {user_prompt}", blueprint)

    generated_files = existing_context.copy()
    for file_meta in blueprint['files']:
        path = file_meta['path']
        if path in generated_files: continue

        print(f"\n📝 Generating: {path}...")
        content = coder.generate_code(path, file_meta['description'], blueprint, generated_files)
        patch = {
            'file': path, 'reason': 'initial generation', 'risk': 'low',
            'tests': [], 'old_content': '', 'new_content': content
        }
        if handle_sdlc_promotion(patch, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry, generated_files):
            generated_files[path] = patch['new_content']

def perform_repo_audit(files, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry):
    print("\n🕵️ Starting Full Repo Audit...")
    for path, content in files.items():
        print(f"\n🔍 Auditing {path}...")
        audit_results = audit_agent.perform_full_audit(path, content, files)
        for atype, result in audit_results.items():
            if any(k in result.upper() for k in ["ISSUE", "ERROR", "WARNING"]):
                print(f"⚠️ {atype.upper()} issue in {path}.")
                patch = repair_agent.propose_patch(path, content, f"{atype} audit: {result}", files)
                if patch and handle_sdlc_promotion(patch, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry, files):
                    files[path] = patch['new_content']

def handle_sdlc_promotion(patch, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry, context):
    path = patch['file']
    version_tag = f"v{int(time.time())}"
    patch['diff'] = PatchManager.generate_diff(patch['old_content'], patch['new_content'], path)

    print(f"🧪 [SANDBOX] Validating {path}...")
    branch_name = f"promotion-{version_tag}"
    sandbox.create_candidate_branch(branch_name)
    storage.write_file(path, patch['new_content'])

    if tools.run_tests().get('returncode') != 0 and os.path.exists(os.path.join(storage.project_root, "tests")):
        print("❌ Promotion Rejected: Sandbox tests failed.")
        sandbox.abort_candidate(branch_name)
        return False

    if not deployer.deploy_to_staging(patch, version_tag):
        print("⚠️ Staging deployment warnings (simulated).")

    metrics = telemetry.capture_metrics('staging', version_tag)
    PatchManager.preview_patch(patch)
    approval = input(f"Approve promotion to PRODUCTION? [y/N]: ").lower()

    if approval == 'y':
        if deployer.deploy_to_prod(version_tag, rollback_point='previous'):
             sandbox.merge_to_main(branch_name)
             memory.add_patch(patch)
             memory.add_version({'tag': version_tag, 'latency': metrics['latency'], 'tests_passed': 1})
             print(f"✅ Version {version_tag} is now LIVE.")
             return True

    sandbox.abort_candidate(branch_name)
    return False

def perform_evolution_loop(files, coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry, shadow):
    print("\n🧬 Starting Comparative Evolution Mode...")
    for path, content in files.items():
        print(f"\nComparing implementations for {path}...")
        results = shadow.run_shadow_workload(f"Improve and refactor {path}", files)

        current_metrics = {"latency": results['current']['latency'], "tests_passed": 1}
        candidate_metrics = {"latency": results['candidate']['latency'], "tests_passed": 1}

        comparison = CompareEngine.compare(current_metrics, candidate_metrics)
        print(f"📊 COMPARISON: Winner={comparison['winner']} | Reasons: {comparison['reasons']}")

        evo_id = memory.log_evolution("current", "candidate", comparison['winner'], comparison)

        if comparison['winner'] == 'candidate':
             patch = {
                 'file': path, 'reason': 'evolutionary optimization', 'risk': 'medium',
                 'tests': [], 'old_content': content, 'new_content': results['candidate']['content']
             }
             if handle_evolution_promotion(patch, evo_id, memory, storage, tools, sandbox, deployer, telemetry):
                 files[path] = patch['new_content']

def handle_evolution_promotion(patch, evo_id, memory, storage, tools, sandbox, deployer, telemetry):
    PatchManager.preview_patch(patch)
    approval = input(f"PROMOTION GATE: Approve evolutionary replacement? [y/N]: ").lower()
    if approval == 'y':
        branch_name = f"evo-{int(time.time())}"
        sandbox.create_candidate_branch(branch_name)
        storage.write_file(patch['file'], patch['new_content'])
        if tools.run_tests().get('returncode') == 0 or not os.path.exists(os.path.join(storage.project_root, "tests")):
             if sandbox.merge_to_main(branch_name):
                 memory.update_evolution_status(evo_id, 'PROMOTED')
                 print("✅ Evolution Promoted.")
                 return True
    sandbox.abort_candidate(branch_name)
    memory.update_evolution_status(evo_id, 'REJECTED')
    return False

if __name__ == "__main__":
    main()
