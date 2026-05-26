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
    print("🤖 Improvised Mini Jules Agent")
    print("="*50 + "\n")

    router = ProviderRouter()
    project_dir = input("Project Name: ").strip() or "improv_project"
    storage = Storage(project_dir)
    tools = ToolExecutor(project_dir)
    manifest = ProjectManifest(storage.project_root)
    session = SessionManager(storage.project_root)

    planner = PlannerAgent(router)
    coder = CoderAgent(router)
    critique_agent = CritiqueAgent(router)
    repair_agent = RepairAgent(router)

    # 1. Blueprint Phase
    user_prompt = input("Build goal: ")
    blueprint = planner.create_blueprint(user_prompt)
    if not blueprint: return

    # 2. Initialization
    manifest.create(user_prompt, "python-v1", [f['path'] for f in blueprint['files']])
    generated_files = {}

    for file_meta in blueprint['files']:
        path = file_meta['path']
        print(f"\n📝 Generating: {path}...")
        content = coder.generate_file(path, file_meta['description'], blueprint, generated_files)

        # 3. Validation
        critique = critique_agent.analyze(path, content, blueprint, generated_files)
        if critique.get('verdict') == "FAIL":
            print(f"🛠️  Repairing {path}...")
            patch = repair_agent.propose_patch(path, content, critique['issues'], blueprint, generated_files)
            if patch: content = patch['new_content']

        # 4. Human Gate & Export
        print(f"\n--- Export Ready: {path} ---")
        if input(f"Approve writing {path}? [y/N]: ").lower() == 'y':
            if storage.write_file(path, content, interactive=False):
                generated_files[path] = content
                manifest.log_approval(path)
                session.save_session(blueprint, generated_files, [], [p for p in generated_files])

    manifest.update_field("status", "exported")
    print(f"\n✅ Project '{blueprint.get('project_name')}' Exported to {project_dir}")

if __name__ == "__main__":
    main()
