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
from project_creator.router.provider_router import ProviderRouter
from project_creator.agents.planner_agent import PlannerAgent
from project_creator.agents.coder_agent import CoderAgent
from project_creator.agents.repair_agent import AuditAgent, RepairAgent

def main():
    print("\n" + "="*60)
    print("🚀 Development Operating System v4")
    print("="*60 + "\n")

    router = ProviderRouter()
    project_dir = input("Enter project directory: ").strip() or "dev_os_v4"
    storage = Storage(project_dir)
    tools = ToolExecutor(project_dir)
    memory = MemoryLayer(os.path.join(storage.project_root, ".agent_memory.db"))
    sandbox = Sandbox(project_dir)

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

    if existing_context:
        mode = input("\n[G]enerate new, [A]udit existing, or [P]reference setup? [G/a/p]: ").lower()
    else:
        mode = 'g'

    if mode == 'p':
        setup_preferences(memory)
    elif mode == 'a':
        perform_repo_audit(existing_context, audit_agent, repair_agent, memory, storage, tools, sandbox)
    else:
        perform_generation_flow(planner, coder, audit_agent, repair_agent, memory, storage, tools, sandbox)

def setup_preferences(memory):
    print("\n⚙️  Preference Setup")
    pref_key = input("Preference key (e.g., 'style'): ")
    pref_val = input("Value (e.g., 'prefer async/await'): ")
    memory.update_preference(pref_key, pref_val)
    print("✅ Preference saved.")

def perform_generation_flow(planner, coder, audit_agent, repair_agent, memory, storage, tools, sandbox):
    user_prompt = input("What would you like to build?\n> ")
    existing_context = storage.read_existing_files()

    blueprint = planner.create_blueprint(user_prompt, list(existing_context.keys()))
    generated_files = existing_context.copy()

    for i, file_meta in enumerate(blueprint['files']):
        path = file_meta['path']
        if path in generated_files: continue

        print(f"\n📝 Generating ({i+1}/{len(blueprint['files'])}): {path}...")
        try:
            content = coder.generate_code(path, file_meta['description'], blueprint, generated_files)
            patch = {
                'file': path,
                'reason': 'initial generation',
                'risk': 'low',
                'tests': [],
                'old_content': '',
                'new_content': content
            }
            if handle_patch_promotion(patch, audit_agent, repair_agent, memory, storage, tools, sandbox, generated_files):
                generated_files[path] = patch['new_content']
        except Exception as e:
            print(f"❌ Error: {e}")

def perform_repo_audit(files, audit_agent, repair_agent, memory, storage, tools, sandbox):
    print("\n🕵️ Starting Full Repository Audit...")
    for path, content in files.items():
        print(f"\n🔍 Auditing {path}...")
        audit_results = audit_agent.perform_full_audit(path, content, files)

        for atype, result in audit_results.items():
            memory.log_audit(path, atype, result)
            if any(k in result.upper() for k in ["ISSUE", "ERROR", "WARNING"]):
                print(f"⚠️ {atype.upper()} Audit found issues in {path}.")
                patch = repair_agent.propose_patch(path, content, f"{atype} audit: {result}", files)
                if patch:
                    if handle_patch_promotion(patch, audit_agent, repair_agent, memory, storage, tools, sandbox, files):
                        files[path] = patch['new_content']

def handle_patch_promotion(patch, audit_agent, repair_agent, memory, storage, tools, sandbox, context):
    path = patch['file']
    patch['diff'] = PatchManager.generate_diff(patch['old_content'], patch['new_content'], path)

    # 🧪 Promotion Gate Prep
    print(f"🧪 Promotion Gate: Measuring impact for {path}...")

    # Measure Before
    start_tests = time.time()
    tools.run_tests()
    latency_before = time.time() - start_tests

    # Create Sandbox Branch
    branch_name = f"patch-{int(time.time())}"
    sandbox.create_candidate_branch(branch_name)

    # Apply to sandbox
    storage.write_file(path, patch['new_content'])

    # Measure After
    start_tests = time.time()
    tools.run_tests()
    latency_after = time.time() - start_tests

    # Preview
    PatchManager.preview_patch(patch)
    print(f"📊 IMPACT: Latency {latency_before:.2f}s -> {latency_after:.2f}s")

    approval = input(f"Approve this change and promotion? [Y]es, [N]o: ").lower()

    impact_data = {
        'latency_before': latency_before,
        'latency_after': latency_after,
        'tests_before': 0, # Simplified
        'tests_after': 0
    }

    if approval == 'y' and latency_after <= latency_before * 1.1: # Allow slight variance
        patch_id = memory.add_patch(patch)
        memory.update_patch_impact(patch_id, impact_data)

        if sandbox.merge_to_main(branch_name):
            memory.update_patch_status(patch_id, 'APPROVED')
            print("✅ Promotion Successful. Merged to main.")

            # Record Version
            memory.add_version({
                'tag': f"v{int(time.time())}",
                'latency': latency_after,
                'tests_passed': 1
            })
            return True
    else:
        if approval == 'y':
            print("❌ Promotion Rejected: Performance regression detected.")
        else:
            print("❌ Promotion Rejected by Human.")
        sandbox.abort_candidate(branch_name)
        patch_id = memory.add_patch(patch)
        memory.update_patch_status(patch_id, 'REJECTED')
        memory.update_patch_impact(patch_id, impact_data)

    return False

if __name__ == "__main__":
    main()
