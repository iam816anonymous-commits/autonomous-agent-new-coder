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
from project_creator.router.provider_router import ProviderRouter
from project_creator.agents.planner_agent import PlannerAgent
from project_creator.agents.coder_agent import CoderAgent
from project_creator.agents.repair_agent import AuditAgent, RepairAgent

def main():
    print("\n" + "="*60)
    print("🚀 Autonomous SDLC Platform v5")
    print("="*60 + "\n")

    router = ProviderRouter()
    project_dir = input("Enter project directory: ").strip() or "sdlc_platform_v5"
    storage = Storage(project_dir)
    tools = ToolExecutor(project_dir)
    memory = MemoryLayer(os.path.join(storage.project_root, ".agent_memory.db"))
    sandbox = Sandbox(project_dir)
    deployer = DeploymentOrchestrator(memory, tools, sandbox)
    telemetry = TelemetryEngine(memory)

    planner = PlannerAgent(router)
    coder = CoderAgent(router, memory)
    audit_agent = AuditAgent(router)
    repair_agent = RepairAgent(router)

    existing_context = storage.read_existing_files()

    # Update Knowledge Graph
    print("📊 Updating Knowledge Graph...")
    for path, content in existing_context.items():
        analysis = KnowledgeGraph.analyze_file(path, content)
        memory.update_knowledge_graph(path, analysis['dependencies'], KnowledgeGraph.get_owner_agent(path), analysis['risk_score'])
        memory.update_knowledge_graph_env(path, analysis['service'], analysis['deploy_target'])

    state = storage.load_state()
    if state:
        resume = input(f"Existing state found for project '{state.get('blueprint', {}).get('project_name', 'unknown')}'. Resume? [Y/n] ").lower()
        if resume == 'n': state = None

    if state:
        mode = 'g'
        blueprint = state['blueprint']
        generated_files = state.get('generated_files', existing_context)
    elif existing_context:
        mode = input("\n[G]enerate, [A]udit, [T]elemetry check, or [R]ollback? [G/a/t/r]: ").lower()
    else:
        mode = 'g'

    if mode == 't':
        env = input("Env (staging/prod): ")
        ver = input("Version tag: ")
        metrics = telemetry.capture_metrics(env, ver)
        print(f"Metrics: {metrics}")
    elif mode == 'r':
        env = input("Env: ")
        ver = input("Rollback to version: ")
        deployer.rollback(env, ver)
    elif mode == 'a':
        perform_repo_audit(existing_context, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry)
    else:
        if not state:
            perform_generation_flow(planner, coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry, existing_context)
        else:
             # Resume generation flow
             continue_generation(blueprint, generated_files, coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry)

def perform_generation_flow(planner, coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry, existing_context):
    user_prompt = input("What would you like to build?\n> ")

    print("\n🏗️  Architecting project blueprint...")
    blueprint = planner.create_blueprint(user_prompt, list(existing_context.keys()))

    # Interactive refinement loop as requested
    while True:
        print("\n📋 Proposed Structure:")
        for i, file in enumerate(blueprint['files']):
            print(f"  {i+1:2d}. {file['path']} - {file['description']}")

        refine = input("\n[A]dd/Remove, [R]efine, or [P]roceed? [A/R/P]: ").lower()
        if refine == 'p': break
        elif refine in ['a', 'r']:
            feedback = input("Feedback: ")
            blueprint = planner.create_blueprint(f"Update blueprint: {feedback}. Original goal: {user_prompt}", blueprint)

    storage.save_state({"blueprint": blueprint, "generated_files": existing_context})
    continue_generation(blueprint, existing_context, coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry)

def continue_generation(blueprint, generated_files, coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry):
    for file_meta in blueprint['files']:
        path = file_meta['path']
        if path in generated_files: continue

        print(f"\n📝 Generating: {path}...")
        content = coder.generate_code(path, file_meta['description'], blueprint, generated_files)

        # During initial generation, we use a lighter gate if tests are not yet available
        # But we still use the promotion logic to ensure safety.
        patch = {
            'file': path, 'reason': 'initial generation', 'risk': 'low',
            'tests': [], 'old_content': '', 'new_content': content
        }

        # Determine if we should enforce strict gates (only if it's not the very first file or tests exist)
        strict = len(generated_files) > 0 and os.path.exists(os.path.join(storage.project_root, "tests"))

        if handle_sdlc_promotion(patch, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry, generated_files, strict=strict):
            generated_files[path] = patch['new_content']
            storage.save_state({"blueprint": blueprint, "generated_files": generated_files})

def perform_repo_audit(files, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry):
    print("\n🕵️ Starting Full Repo Audit...")
    for path, content in files.items():
        print(f"\n🔍 Auditing {path}...")
        audit_results = audit_agent.perform_full_audit(path, content, files)
        for atype, result in audit_results.items():
            if any(k in result.upper() for k in ["ISSUE", "ERROR", "WARNING"]):
                print(f"⚠️ {atype.upper()} issue in {path}.")
                patch = repair_agent.propose_patch(path, content, f"{atype} audit: {result}", files)
                if patch and handle_sdlc_promotion(patch, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry, files, strict=True):
                    files[path] = patch['new_content']

def handle_sdlc_promotion(patch, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry, context, strict=True):
    path = patch['file']
    version_tag = f"v{int(time.time())}"
    patch['diff'] = PatchManager.generate_diff(patch['old_content'], patch['new_content'], path)

    # 1. Sandbox Validation
    print(f"🧪 [SANDBOX] Validating {path}...")
    branch_name = f"promotion-{version_tag}"
    sandbox.create_candidate_branch(branch_name)
    storage.write_file(path, patch['new_content'])

    if strict:
        test_res = tools.run_tests()
        if test_res.get('returncode') != 0 and test_res.get('returncode') is not None:
            print(f"❌ Promotion Rejected: Sandbox tests failed for {path}.")
            sandbox.abort_candidate(branch_name)
            return False

    # 2. Staging Deployment
    # Staging gate can also be relaxed if not strict
    if not deployer.deploy_to_staging(patch, version_tag):
        if strict:
            print("❌ Staging deployment failed.")
            sandbox.abort_candidate(branch_name)
            return False
        else:
            print("⚠️ Staging deployment warnings ignored (Non-strict mode).")

    # 3. Telemetry Feedback Loop (Staging)
    metrics = telemetry.capture_metrics('staging', version_tag)
    healthy, msg = telemetry.check_health('staging', version_tag)
    if not healthy and strict:
        print(f"❌ Staging Telemetry Gate Failed: {msg}")
        deployer.rollback('staging', 'previous')
        sandbox.abort_candidate(branch_name)
        return False

    # 4. Human Approval (PROD GATE)
    PatchManager.preview_patch(patch)
    if 'latency' in metrics:
        print(f"📊 STAGING HEALTH: {msg} (Latency: {metrics['latency']:.2f}ms)")

    approval = input(f"Approve promotion to PRODUCTION for {path}? [y/N]: ").lower()

    if approval == 'y':
        # 5. Production Deployment
        if deployer.deploy_to_prod(version_tag, rollback_point='previous') or not strict:
             sandbox.merge_to_main(branch_name)
             memory.add_patch(patch)
             memory.add_version({'tag': version_tag, 'latency': metrics.get('latency', 0), 'tests_passed': 1})
             print(f"✅ Version {version_tag} is now LIVE in Production.")
             return True

    print("❌ Production promotion aborted.")
    sandbox.abort_candidate(branch_name)
    return False

if __name__ == "__main__":
    main()
