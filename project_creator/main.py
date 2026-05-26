import os
import json
import sys

# Ensure project_root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_creator.core.storage import Storage
from project_creator.core.tools import ToolExecutor
from project_creator.core.manifest import ProjectManifest
from project_creator.core.session import SessionManager
from project_creator.router.provider_router import ProviderRouter
from project_creator.agents.planner_agent import PlannerAgent
from project_creator.agents.coder_agent import CoderAgent
from project_creator.agents.critique_agent import CritiqueAgent
from project_creator.agents.repair_agent import RepairAgent

def main():
    print("\n" + "="*50)
    print("🤖 Production-Hardened Mini Jules Agent")
    print("="*50 + "\n")

    router = ProviderRouter()
    project_dir = input("Project Name: ").strip() or "final_jules_app"
    storage = Storage(project_dir)
    tools = ToolExecutor(project_dir)
    manifest = ProjectManifest(storage.project_root)
    session = SessionManager(storage.project_root)

    planner = PlannerAgent(router)
    coder = CoderAgent(router)
    critique_agent = CritiqueAgent(router)
    repair_agent = RepairAgent(router)

    # Session Resume Logic
    s_data = session.load_session()
    if s_data:
        if input(f"Resume session for '{s_data['blueprint'].get('project_name')}'? [Y/n] ").lower() != 'n':
            blueprint = s_data['blueprint']
            generated_files = s_data['generated_files']
        else: s_data = None

    if not s_data:
        user_prompt = input("Describe your build goal: ")
        print("\n🏗️  Phase 1: Architecture Planning...")
        blueprint = planner.create_blueprint(user_prompt)
        if not blueprint:
            print("❌ Failure: Could not generate blueprint.")
            return

        print(f"\n📋 Blueprint Received: {blueprint.get('project_name')}")
        for f in blueprint.get('files', []):
            print(f"  - {f['path']}: {f['description']}")

        manifest.create(user_prompt, "python-vFinal", [f['path'] for f in blueprint['files']])
        generated_files = {}

    # Phase 2: Implementation & Validation Loop
    for file_meta in blueprint.get('files', []):
        path = file_meta['path']
        if path in generated_files: continue

        print(f"\n📝 Phase 2: Generating {path}...")
        content = coder.generate_file(path, file_meta['description'], blueprint, generated_files)

        # Iterative SDLC Loop
        while True:
            print(f"🔍 Phase 3: Auditing {path}...")
            critique = critique_agent.analyze(path, content, blueprint, generated_files)

            if critique['verdict'] == 'PASS':
                print(f"✅ Audit Passed ({critique.get('security_score', 'N/A')}/10)")
                break

            print(f"🛠️  Phase 4: Proposing Repair for {path}...")
            print(f"Issues: {', '.join(critique['issues'])}")
            patch = repair_agent.propose_patch(path, content, critique['issues'], blueprint, generated_files)
            if patch and patch.get('status') == 'pending':
                print("\n--- Repair Proposed ---")
                print(f"Reason: {patch.get('reason')}")
                if input("Apply this patch? [y/N]: ").lower() == 'y':
                    content = patch['new_content']
                else: break
            else: break

        # Phase 5: Human Approval & Persistence
        print(f"\n--- Final Review for {path} ---")
        print(content[:600] + ("..." if len(content) > 600 else ""))
        print("-" * 30)

        choice = input("[C]onfirm Write, [E]dit, [S]kip, [R]egenerate? ").lower()
        if choice == 'c':
            if storage.write_file(path, content, interactive=True):
                generated_files[path] = content
                manifest.log_approval(path)
                session.save_session(blueprint, generated_files, [], [p for p in generated_files])
                if path.endswith(".py"): tools.run_format(path)
        elif choice == 'e':
            content = sys.stdin.read()
            if storage.write_file(path, content, interactive=False):
                generated_files[path] = content
                session.save_session(blueprint, generated_files, [], [p for p in generated_files])
        elif choice == 'r': continue
        else: print(f"⏭️  Skipped {path}")

    manifest.update_field("status", "ready")
    print(f"\n🚀 Mission Accomplished: Project '{blueprint.get('project_name')}' generated!")

if __name__ == "__main__":
    main()
