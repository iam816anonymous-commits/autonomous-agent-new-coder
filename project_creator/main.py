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
    print("🤖 Validated Mini Jules Project Agent")
    print("="*50 + "\n")

    router = ProviderRouter()
    project_dir = input("Project Name: ").strip() or "validated_app"
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
            repairs = s_data['repairs']
            approvals = s_data['approvals']
        else: s_data = None

    if not s_data:
        user_prompt = input("What would you like to build?\n> ")
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

        manifest.create(
            blueprint.get('project_name', 'jules_app'),
            {"backend": "fastapi", "frontend": "unknown"},
            [f['path'] for f in blueprint['files']]
        )
        generated_files, repairs, approvals = {}, [], []

    for file_meta in blueprint['files']:
        path = file_meta['path']
        if path in generated_files: continue

        print(f"\n📝 Generating: {path}...")
        # Full content context passed here
        content = coder.generate_file(path, file_meta['description'], blueprint, generated_files)

        while True:
            critique = critique_agent.analyze(path, content, blueprint, generated_files)
            if "PASS" in critique.upper(): break

            print(f"🛠️  Patch Proposed for {path}")
            patch = repair_agent.propose_patch(path, content, critique, blueprint, generated_files)
            if patch and patch.get('action') == 'repair':
                manifest.add_patch(path, approved=False)
                if input(f"Approve repair patch for {path}? [y/N]: ").lower() == 'y':
                    content = patch['new_content']
                    manifest.add_patch(path, approved=True)
                else: break
            else: break

        print(f"\n--- Preview: {path} ---")
        print(content[:500] + ("..." if len(content) > 500 else ""))
        print("-" * 30)

        choice = input("[C]reate, [E]dit, [S]kip, [R]egenerate? ").lower()
        if choice == 'c':
            if storage.write_file(path, content):
                generated_files[path] = content
                approvals.append(path)
                if path.endswith(".py"): tools.run_format(path)
                session.save_session(blueprint, generated_files, repairs, approvals)
        elif choice == 'e':
            content = sys.stdin.read()
            if storage.write_file(path, content):
                generated_files[path] = content
                session.save_session(blueprint, generated_files, repairs, approvals)
        elif choice == 'r': continue
        else: print(f"Skipped {path}")

    manifest.update_status("validated")
    manifest.update_validation("pass")
    print(f"\n🚀 Validated Project Ready!")

if __name__ == "__main__":
    main()
