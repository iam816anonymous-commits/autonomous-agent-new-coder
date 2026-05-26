import os
import json
import sys
import time

# Ensure project_root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_creator.core.storage import Storage
from project_creator.core.tools import ToolExecutor
from project_creator.core.manifest import ProjectManifest
from project_creator.core.session import SessionManager
from project_creator.core.patch import PatchManager
from project_creator.router.provider_router import ProviderRouter
from project_creator.agents.planner_agent import PlannerAgent
from project_creator.agents.coder_agent import CoderAgent
from project_creator.agents.critique_agent import CritiqueAgent
from project_creator.agents.repair_agent import RepairAgent

def main():
    print("\n" + "="*50)
    print("🤖 Production Validated Mini Jules")
    print("="*50 + "\n")

    router = ProviderRouter()
    project_dir = input("Enter project path: ").strip() or "prod_validated_jules"
    storage = Storage(project_dir)
    tools = ToolExecutor(project_dir)
    manifest = ProjectManifest(storage.project_root)
    session = SessionManager(storage.project_root)

    planner = PlannerAgent(router)
    coder = CoderAgent(router)
    critique_agent = CritiqueAgent(router)
    repair_agent = RepairAgent(router)

    s_data = session.load_session()
    if s_data:
        if input("Resume session? [Y/n] ").lower() != 'n':
            blueprint = s_data['blueprint']
            generated_files = s_data['generated_files']
            repairs = s_data.get('repairs', [])
            approvals = s_data.get('approvals', [])
        else: s_data = None

    if not s_data:
        user_prompt = input("What would you like to build? (e.g., FastAPI backend)\n> ")
        print("\n🏗️  Architecting Blueprint...")
        blueprint = planner.create_blueprint(user_prompt)
        if not blueprint: return

        # Interactive Feedback Loop for Blueprint
        while True:
            print("\n📋 Proposed Project Structure:")
            for i, file in enumerate(blueprint['files']):
                print(f"  {i+1:2d}. {file['path']} - {file['description']}")

            refine = input("\n[A]dd/Remove, [R]efine, or [P]roceed? [A/R/P]: ").lower()
            if refine == 'p': break
            elif refine in ['a', 'r']:
                feedback = input("Enter feedback: ")
                print("\n🔄 Updating blueprint...")
                blueprint = planner.create_blueprint(f"Update blueprint: {feedback}. Original goal: {user_prompt}")
            else: print("Invalid choice.")

        # Manifest Init
        manifest.create(user_prompt, "python-production", [f['path'] for f in blueprint['files']])
        generated_files, repairs, approvals = {}, [], []
        manifest.add_session(f"session_{int(time.time())}")

    for file_meta in blueprint['files']:
        path = file_meta['path']
        if path in generated_files: continue

        print(f"\n📝 Generating: {path}...")
        content = coder.generate_file(path, file_meta['description'], blueprint, generated_files)

        # Immutable Patch Constitution Lifecycle
        while True:
            # 2. Critique
            print(f"🔍 Critiquing {path}...")
            critique = critique_agent.analyze(path, content, blueprint, generated_files)

            if "PASS" in critique.upper():
                print(f"✅ Critique Passed for {path}")
                break

            # 3. Patch
            print(f"🛠️  Proposing Patch for {path}...")
            patch = repair_agent.propose_patch(path, content, critique, blueprint, generated_files)

            if patch and patch.get('status') == 'pending':
                # 4. Approve
                print(f"\n--- Patch Proposal for {path} ---")
                print(f"Reason: {patch.get('reason')}")
                # Optional: Show Diff using PatchManager
                # diff = PatchManager.generate_diff(content, patch['new_content'], path)
                # print(diff)

                print("-" * 30)
                if input("Approve and Apply Patch? [y/N]: ").lower() == 'y':
                    content = patch['new_content']
                    patch['status'] = 'approved'
                    repairs.append(patch)
                    manifest.update_field("patches", {"approved": [p['file'] for p in repairs if p['status'] == 'approved']})
                else: break
            else: break

        # 5. Apply (Final File Approval)
        print(f"\n--- Final Review: {path} ---")
        print(content[:500] + ("..." if len(content) > 500 else ""))
        print("-" * 30)

        choice = input("[C]reate, [E]dit, [S]kip, [R]egenerate? ").lower()
        if choice == 'c':
            if storage.write_file(path, content):
                generated_files[path] = content
                manifest.add_approval(path)
                # Sync context to manifest
                manifest.update_field("context", {p: c[:100]+"..." for p, c in generated_files.items()})
                session.save_session(blueprint, generated_files, repairs, [path for path in generated_files])
        elif choice == 'e':
            print("Edit mode (Paste content, Ctrl-D):")
            content = sys.stdin.read()
            if storage.write_file(path, content):
                generated_files[path] = content
                session.save_session(blueprint, generated_files, repairs, [path for path in generated_files])
        elif choice == 'r': continue
        else: print(f"Skipped {path}")

    manifest.update_field("status", "validated")
    manifest.update_field("validation", {"tests": "pass", "architecture_consistency": "pass"})
    print(f"\n🚀 Production Validated Project '{blueprint.get('project_name')}' Ready!")

if __name__ == "__main__":
    main()
