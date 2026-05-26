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
from project_creator.core.evolution import CompareEngine, ShadowExecutor, DriftDetector
from project_creator.router.provider_router import ProviderRouter
from project_creator.agents.planner_agent import PlannerAgent
from project_creator.agents.coder_agent import CoderAgent
from project_creator.agents.repair_agent import AuditAgent, RepairAgent

def main():
    print("\n" + "="*60)
    print("🧬 Evidence-based Evolution Platform v7")
    print("="*60 + "\n")

    router = ProviderRouter()
    project_dir = input("Enter project directory: ").strip() or "evolution_v7"
    storage = Storage(project_dir)
    tools = ToolExecutor(project_dir)
    memory = MemoryLayer(os.path.join(storage.project_root, ".agent_memory.db"))
    sandbox = Sandbox(project_dir)
    deployer = DeploymentOrchestrator(memory, tools, sandbox)
    telemetry = TelemetryEngine(memory)

    planner = PlannerAgent(router)
    coder = CoderAgent(router, memory)
    shadow = ShadowExecutor(coder, tools)

    audit_agent = AuditAgent(router)
    repair_agent = RepairAgent(router)

    existing_context = storage.read_existing_files()

    if not memory.get_champion_version():
        memory.add_version({'tag': 'v1.0', 'is_champion': True, 'latency': 100, 'tests_passed': 1})

    mode = input("\n[G]enerate, [A]udit, or [E]volve? [G/a/e]: ").lower()

    if mode == 'e':
        perform_evidence_based_evolution(existing_context, coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry, shadow)
    elif mode == 'a':
        perform_repo_audit(existing_context, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry)
    else:
        perform_generation_flow(planner, coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry)

def perform_generation_flow(planner, coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry):
    user_prompt = input("What would you like to build?\n> ")
    existing_context = storage.read_existing_files()
    blueprint = planner.create_blueprint(user_prompt, list(existing_context.keys()))

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

def perform_evidence_based_evolution(files, champion_agent, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry, shadow):
    print("\n🧬 Starting Evidence-based Evolution...")
    champ_info = memory.get_champion_version()
    champ_ver, champ_lat, champ_cost, champ_tests = champ_info
    champ_metrics = {"latency": champ_lat, "cost": champ_cost, "tests_passed": champ_tests}

    for path, content in files.items():
        print(f"\nEvaluating Evolution for {path}...")
        results = shadow.run_shadow_workload(f"Advanced optimization for {path}", files, [champion_agent, champion_agent])

        for cid, cres in results.items():
            if cid == "champion": continue

            print(f"📉 Analyzing {cid} for {path}...")
            candidate_metrics = {"latency": cres['latency'], "cost": 0.5, "tests_passed": 1, "approval_rate": 0.9, "repair_success": 0.85}

            drift, msg = DriftDetector.detect(champ_metrics, candidate_metrics)
            if drift:
                print(f"❌ {cid} REJECTED: {msg}")
                continue

            scorecard = CompareEngine.generate_scorecard(cid, champ_metrics, candidate_metrics)
            print(f"\n📊 SCORECARD for {cid}:")
            print(json.dumps(scorecard, indent=2))

            approval = input(f"PROMOTION GATE: Approve this challenger? [y/N]: ").lower()
            if approval == 'y':
                scorecard['promotion'] = 'approved'
                memory.add_scorecard(scorecard)
                version_tag = f"v{int(time.time())}"
                patch = {'file': path, 'reason': f"Evolution: {cid}", 'risk': 'low', 'tests': [], 'old_content': content, 'new_content': cres['content']}

                if handle_evolution_promotion(patch, version_tag, champ_ver, memory, storage, tools, sandbox, deployer, telemetry):
                    memory.add_version({'tag': version_tag, 'parent': champ_ver, 'is_champion': True, 'latency': candidate_metrics['latency'], 'tests_passed': 1})
                    return

def handle_evolution_promotion(patch, version_tag, parent_ver, memory, storage, tools, sandbox, deployer, telemetry):
    PatchManager.preview_patch(patch)
    branch_name = f"evo-{version_tag}"
    sandbox.create_candidate_branch(branch_name)
    storage.write_file(patch['file'], patch['new_content'])
    if tools.run_tests().get('returncode') == 0 or not os.path.exists(os.path.join(storage.project_root, "tests")):
        if sandbox.merge_to_main(branch_name):
            return True
    sandbox.abort_candidate(branch_name)
    return False

if __name__ == "__main__":
    main()
