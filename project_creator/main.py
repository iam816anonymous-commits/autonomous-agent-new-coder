import os
import json
import sys

# Ensure sys.path includes project_root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_creator.core.storage import Storage
from project_creator.core.tools import ToolExecutor
from project_creator.router.provider_router import ProviderRouter
from project_creator.agents.planner_agent import PlannerAgent
from project_creator.agents.coder_agent import CoderAgent
from project_creator.agents.repair_agent import CritiqueAgent, RepairAgent

def main():
    print("\n" + "="*50)
    print("🤖 Mini Jules Project Generator")
    print("="*50 + "\n")

    router = ProviderRouter()
    project_dir = input("Enter project name: ").strip() or "my_jules_project"
    storage = Storage(project_dir)
    tools = ToolExecutor(project_dir)

    planner = PlannerAgent(router)
    coder = CoderAgent(router)
    critique_agent = CritiqueAgent(router)
    repair_agent = RepairAgent(router)

    state = storage.load_state()
    if state:
        resume = input(f"Existing state found for '{state['blueprint'].get('project_name')}'. Resume? [Y/n] ").lower()
        if resume != 'n':
            blueprint = state['blueprint']
            generated_files = state.get('generated_files', {})
        else:
            state = None

    if not state:
        user_prompt = input("What would you like to build? (e.g., SaaS with Next.js & FastAPI)\n> ")
        print("\n🏗️  Architecting Blueprint...")
        blueprint = planner.create_blueprint(user_prompt)
        if not blueprint:
            print("❌ Failed to generate blueprint.")
            return
        generated_files = {}

    print(f"\n📋 Project Architecture: {blueprint.get('project_name')}")
    for file in blueprint.get('files', []):
        status = "✅" if file['path'] in generated_files else "⏳"
        print(f"  {status} {file['path']}")

    for file_meta in blueprint.get('files', []):
        path = file_meta['path']
        if path in generated_files: continue

        print(f"\n📝 Generating: {path}...")

        # Iterative Generate-Test-Critique-Repair Loop
        content = coder.generate_file(path, file_meta['description'], blueprint, generated_files)

        while True:
            print(f"🔍 Critiquing {path}...")
            critique = critique_agent.analyze(path, content, blueprint, generated_files)

            if "PASS" in critique.upper():
                print(f"✅ Critique Passed for {path}")
                break
            else:
                print(f"🛠️  Repairing {path}...")
                content = repair_agent.repair(path, content, critique, blueprint, generated_files)

        # Human Approval Gate
        print(f"\n--- Preview: {path} ---")
        print(content[:500] + ("..." if len(content) > 500 else ""))
        print("-" * 30)

        choice = input(f"\n[C]reate, [E]dit, [S]kip, [R]egenerate? ").lower()
        if choice == 'c':
            if storage.write_file(path, content):
                generated_files[path] = content
                if path.endswith(".py"): tools.run_format(path)
                # Save state after each successful file
                storage.save_state({"blueprint": blueprint, "generated_files": generated_files})
        elif choice == 'r':
            # Restart loop for this file
            continue
        elif choice == 'e':
            print("Manual Edit: Paste content (Ctrl-D to finish):")
            content = sys.stdin.read()
            if storage.write_file(path, content):
                generated_files[path] = content
                storage.save_state({"blueprint": blueprint, "generated_files": generated_files})
        else:
            print(f"⏭️  Skipping {path}")

    print(f"\n🚀 Exporting Project to '{project_dir}'...")
    print("✅ Project Assembled Successfully!")

if __name__ == "__main__":
    main()
