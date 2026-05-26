import os
import json
import sys

# Ensure the project root is in sys.path to allow consistent absolute imports
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
    print("\n" + "="*60)
    print("🚀 Welcome to the Super Orchestrator Project Creator!")
    print("="*60 + "\n")

    router = ProviderRouter()
    planner = PlannerAgent(router)
    coder = CoderAgent(router)
    critique_agent = CritiqueAgent(router)
    repair_agent = RepairAgent(router)

    project_dir = input("Enter the project directory name (default: 'super_project'): ").strip() or "super_project"
    storage = Storage(project_dir)
    tools = ToolExecutor(project_dir)

    state = storage.load_state()
    blueprint = None
    generated_files = {}

    if state:
        resume = input(f"Existing state found for project '{state['blueprint']['project_name']}'. Resume? [Y/n] ").lower()
        if resume != 'n':
            blueprint = state['blueprint']
            generated_files = state.get('generated_files', {})
            print(f"🔄 Resuming project: {blueprint['project_name']}")
        else:
            state = None

    if not state:
        user_prompt = input("What would you like to build?\n> ")
        existing_context = storage.read_existing_files()
        if existing_context:
            print(f"🔍 Found {len(existing_context)} existing files. Using as context.")

        print("\n🏗️  Architecting project (Primary: Gemini, Fallback: ChatGPT Browser)...")
        blueprint = planner.create_blueprint(user_prompt, list(existing_context.keys()))

        # Interactive refinement
        while True:
            print("\n📋 Proposed Structure:")
            for i, file in enumerate(blueprint['files']):
                print(f"  {i+1:2d}. {file['path']} - {file['description']}")

            refine = input("\n[A]dd/Remove, [R]efine, or [P]roceed? [A/R/P]: ").lower()
            if refine == 'p':
                break
            elif refine in ['a', 'r']:
                feedback = input("Feedback: ")
                blueprint = planner.create_blueprint(f"Update blueprint: {feedback}. Original goal: {user_prompt}", blueprint)

        generated_files.update(existing_context)

    # Code Generation & Critique Pipeline
    files_to_generate = blueprint['files']

    for i, file_meta in enumerate(files_to_generate):
        path = file_meta['path']
        if path in generated_files:
            continue

        print(f"\n📝 Generating ({i+1}/{len(files_to_generate)}): {path}...")
        try:
            # 1. Generation
            content = coder.generate_code(path, file_meta['description'], blueprint, generated_files)

            # 2. Critique
            print(f"🔍 Critiquing {path}...")
            critique = critique_agent.analyze(path, content, generated_files)

            if "PASS" not in critique.upper():
                print(f"🛠️  Repairing {path} based on critique...")
                # 3. Repair
                content = repair_agent.repair(path, content, critique, generated_files)

            # 4. Storage
            if storage.write_file(path, content):
                generated_files[path] = content

                # 5. Tool Use (Linting/Formatting if applicable)
                if path.endswith(".py"):
                    # Only format/lint if tool is available
                    tools.run_format(path)
                    tools.run_lint(path)

                storage.save_state({
                    "blueprint": blueprint,
                    "generated_files": generated_files
                })
        except Exception as e:
            print(f"❌ Error: {e}")
            sys.exit(1)

    # Final Verification
    print("\n🧪 Running final tests...")
    tools.run_tests()

    print(f"\n✅ Project '{blueprint['project_name']}' successfully assembled!")

if __name__ == "__main__":
    main()
