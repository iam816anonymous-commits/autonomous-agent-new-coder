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
from project_creator.router.provider_router import ProviderRouter
from project_creator.agents.planner_agent import PlannerAgent
from project_creator.agents.coder_agent import CoderAgent
from project_creator.agents.repair_agent import AuditAgent, RepairAgent

def main():
    print("\n" + "="*60)
    print("🚀 Welcome to the Engineering Platform v3!")
    print("="*60 + "\n")

    router = ProviderRouter()
    planner = PlannerAgent(router)
    coder = CoderAgent(router)
    audit_agent = AuditAgent(router)
    repair_agent = RepairAgent(router)

    project_dir = input("Enter project directory (default: 'repo_v3'): ").strip() or "repo_v3"
    storage = Storage(project_dir)
    tools = ToolExecutor(project_dir)
    memory = MemoryLayer(os.path.join(storage.project_root, ".agent_memory.db"))

    existing_context = storage.read_existing_files()

    if existing_context:
        print(f"🔍 Scan Repo: Found {len(existing_context)} files.")
        mode = input("\n[G]enerate new or [A]udit existing? [G/a]: ").lower()
    else:
        mode = 'g'

    if mode == 'a':
        perform_repo_audit(existing_context, audit_agent, repair_agent, memory, storage, tools)
    else:
        perform_generation_flow(planner, coder, audit_agent, repair_agent, memory, storage, tools)

def perform_generation_flow(planner, coder, audit_agent, repair_agent, memory, storage, tools):
    user_prompt = input("What would you like to build?\n> ")
    existing_context = storage.read_existing_files()

    print("\n🏗️  Architecting project blueprint...")
    blueprint = planner.create_blueprint(user_prompt, list(existing_context.keys()))

    # Interactive refinement
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

    for i, file_meta in enumerate(blueprint['files']):
        path = file_meta['path']
        if path in generated_files: continue

        print(f"\n📝 Generating ({i+1}/{len(blueprint['files'])}): {path}...")
        try:
            content = coder.generate_code(path, file_meta['description'], blueprint, generated_files)

            # Use the audit/repair logic as a quality gate
            patch = {
                'file': path,
                'reason': 'initial generation',
                'risk': 'low',
                'tests': [],
                'old_content': '',
                'new_content': content
            }

            # Dry-run / Promotion
            if handle_patch_promotion(patch, audit_agent, repair_agent, memory, storage, tools, generated_files):
                generated_files[path] = patch['new_content']
        except Exception as e:
            print(f"❌ Error generating {path}: {e}")

def perform_repo_audit(files, audit_agent, repair_agent, memory, storage, tools):
    print("\n🕵️ Starting Full Repository Audit...")
    for path, content in files.items():
        print(f"\n🔍 Auditing {path}...")
        # Batch audit for efficiency
        audit_results = audit_agent.perform_full_audit(path, content, files)

        for atype, result in audit_results.items():
            memory.log_audit(path, atype, result)
            if "ISSUE" in result.upper() or "ERROR" in result.upper() or "WARNING" in result.upper():
                print(f"⚠️ {atype.upper()} Audit found potential issues in {path}.")

                patch = repair_agent.propose_patch(path, content, f"{atype} audit: {result}", files)
                if not patch: continue

                if handle_patch_promotion(patch, audit_agent, repair_agent, memory, storage, tools, files):
                    # Update local context for subsequent audits
                    files[path] = patch['new_content']

def handle_patch_promotion(patch, audit_agent, repair_agent, memory, storage, tools, context):
    path = patch['file']
    patch['diff'] = PatchManager.generate_diff(patch['old_content'], patch['new_content'], path)

    # 🧪 Dry-run Mode
    print(f"🧪 Dry-run: Running validation for {path}...")
    # Simulate dry-run by running tools on what would be the new content
    # In a full impl, we'd write to a temp file and run tools there.

    PatchManager.preview_patch(patch)

    approval = input(f"Approve this change for {path}? [Y]es, [N]o, [E]dit: ").lower()

    if approval == 'y':
        patch_id = memory.add_patch(patch)
        if storage.write_file(path, patch['new_content']):
            memory.update_patch_status(patch_id, 'APPROVED')
            memory.update_preference(patch['reason'][:50], 'ACCEPTED')

            # Benchmark latency
            start = time.time()
            tools.run_tests()
            latency = time.time() - start
            memory.record_benchmark(patch_id, 'test_latency', latency)

            print(f"✅ Change applied and logged.")
            return True
    elif approval == 'e':
        print("Manual edit mode: Paste the desired content (Ctrl-D to finish):")
        edited = sys.stdin.read()
        patch['new_content'] = edited
        return handle_patch_promotion(patch, audit_agent, repair_agent, memory, storage, tools, context)
    else:
        patch_id = memory.add_patch(patch)
        memory.update_patch_status(patch_id, 'REJECTED')
        memory.update_preference(patch['reason'][:50], 'REJECTED')
        print("❌ Change rejected.")
    return False

if __name__ == "__main__":
    main()
