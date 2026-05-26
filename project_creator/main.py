import os
import json
import sys
import time

# Ensure sys.path includes project_root
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
from project_creator.core.governance import GovernanceLayer, GovernanceSimulator
from project_creator.core.scoreboard import Scoreboard
from project_creator.core.stress_tests import ConstitutionStressTest
from project_creator.router.provider_router import ProviderRouter
from project_creator.agents.planner_agent import PlannerAgent
from project_creator.agents.coder_agent import CoderAgent
from project_creator.agents.repair_agent import AuditAgent, RepairAgent

def main():
    print("\n" + "="*60)
    print("🏛️  Validated Governed Ecosystem v9")
    print("="*60 + "\n")

    router = ProviderRouter()
    project_dir = input("Enter project directory: ").strip() or "validated_v9"
    storage = Storage(project_dir)
    tools = ToolExecutor(project_dir)
    memory = MemoryLayer(os.path.join(storage.project_root, ".agent_memory.db"))
    sandbox = Sandbox(project_dir)
    deployer = DeploymentOrchestrator(memory, tools, sandbox)
    telemetry = TelemetryEngine(memory)
    scoreboard = Scoreboard(os.path.join(storage.project_root, ".agent_memory.db"))
    stress_tester = ConstitutionStressTest(memory)

    planner = PlannerAgent(router)
    coder = CoderAgent(router, memory)
    shadow = ShadowExecutor(coder, tools)
    audit_agent = AuditAgent(router)
    repair_agent = RepairAgent(router)

    existing_context = storage.read_existing_files()

    champ_ver, champ_metrics = memory.get_champion_version()
    if not champ_ver:
        memory.add_version({'tag': 'v1.0', 'is_champion': True, 'metrics': {'latency': 100, 'cost': 1.0, 'tests_passed': 1}})
        champ_ver, champ_metrics = memory.get_champion_version()

    mode = input("\n[G]enerate, [A]udit, [E]volve, [S]coreboard, [V]alidate? [G/a/e/s/v]: ").lower()

    if mode == 's':
        scoreboard.display()
    elif mode == 'v':
        stress_tester.run_stress_tests()
    elif mode == 'e':
        perform_governed_evolution(existing_context, coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry, shadow, champ_ver, champ_metrics)
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
        patch = {'file': path, 'reason': 'initial generation', 'risk': 'low', 'tests': [], 'old_content': '', 'new_content': content}
        if handle_sdlc_promotion(patch, memory, storage, tools, sandbox, deployer, telemetry):
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
                if patch and handle_sdlc_promotion(patch, memory, storage, tools, sandbox, deployer, telemetry):
                    files[path] = patch['new_content']

def handle_sdlc_promotion(patch, memory, storage, tools, sandbox, deployer, telemetry):
    path = patch['file']
    version_tag = f"v{int(time.time())}"
    patch['diff'] = PatchManager.generate_diff(patch['old_content'], patch['new_content'], path)

    branch_name = f"promotion-{version_tag}"
    sandbox.create_candidate_branch(branch_name)
    storage.write_file(path, patch['new_content'])

    if tools.run_tests().get('returncode') != 0 and os.path.exists(os.path.join(storage.project_root, "tests")):
        print("❌ Promotion Rejected: Sandbox tests failed.")
        sandbox.abort_candidate(branch_name)
        return False

    metrics = telemetry.capture_metrics('staging', version_tag)
    PatchManager.preview_patch(patch)
    if input(f"Approve promotion to PRODUCTION for {path}? [y/N]: ").lower() == 'y':
        if deployer.deploy_to_prod(version_tag, rollback_point='previous'):
             sandbox.merge_to_main(branch_name)
             memory.add_patch(patch)
             memory.add_version({'tag': version_tag, 'is_champion': False, 'metrics': {'latency': metrics['latency']}})
             return True

    sandbox.abort_candidate(branch_name)
    return False

def perform_governed_evolution(files, champion_agent, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry, shadow, champ_ver, champ_metrics):
    print("\n🧬 Starting Governed Evolution Loop...")
    for path, content in files.items():
        results = shadow.run_shadow_workload(f"Evolution optimization for {path}", files, [champion_agent])
        for cid, cres in results.items():
            if cid == "champion": continue

            candidate_metrics = {"latency": cres['latency'], "cost": 0.5, "tests_passed": 1}
            violations = GovernanceSimulator.simulate_promotion(candidate_metrics, champ_metrics)
            if violations:
                print(f"❌ Governance Gate Failed for {cid}: {violations}")
                continue

            scorecard = CompareEngine.generate_scorecard(cid, champ_metrics, candidate_metrics)
            print(f"\n📊 SCORECARD: {json.dumps(scorecard, indent=2)}")

            if input(f"Approve promotion of {cid}? [y/N]: ").lower() == 'y':
                scorecard['promotion'] = 'approved'
                memory.add_scorecard(scorecard)
                ver_tag = f"v{int(time.time())}"
                patch = {'file': path, 'reason': f"Evo: {cid}", 'risk': 'low', 'tests': [], 'old_content': content, 'new_content': cres['content']}
                if handle_evolution_promotion(patch, ver_tag, champ_ver, memory, storage, tools, sandbox, deployer, telemetry):
                    memory.add_version({'tag': ver_tag, 'parent': champ_ver, 'is_champion': True, 'metrics': candidate_metrics})
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
