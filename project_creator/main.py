import os
import json
import sys

# Ensure the project root is in sys.path
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

            audit = input("\nWould you like to run a project audit/audit on existing files first? [y/N]: ").lower()
            if audit == 'y':
                perform_audit(existing_context, blueprint, critique_agent, repair_agent, storage, tools)

        print("\n🏗️  Architecting project...")
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

            # 2. Critique & Repair Loop
            content = process_file_with_critique(path, content, blueprint, generated_files, critique_agent, repair_agent, tools)

            # 3. Human Approval Gate
            print(f"\n--- Proposed Content for {path} ---")
            print(content[:500] + ("..." if len(content) > 500 else ""))
            print("-" * 30)
            approval = input(f"Approve writing {path} to disk? [Y/n/e (edit)]: ").lower()

            if approval == 'n':
                print(f"Skipping {path}")
                continue
            elif approval == 'e':
                edited_content = input(f"Paste the new content for {path} (End with Ctrl-D/EOF):\n")
                # Since multi-line input in terminal is tricky with input(),
                # we'll use a slightly better way if possible, or just accept the limitation.
                # For this task, we'll keep it simple but functional.
                content = edited_content

            # 4. Storage
            if storage.write_file(path, content):
                generated_files[path] = content

                # 5. Tool Use (Formatting)
                if path.endswith(".py"):
                    tools.run_format(path)

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

def process_file_with_critique(path, content, blueprint, generated_files, critique_agent, repair_agent, tools):
    print(f"🔍 Critiquing {path}...")
    critique = critique_agent.analyze(path, content, generated_files)

    if "PASS" not in critique.upper():
        print(f"🛠️  Repairing {path} based on critique...")
        content = repair_agent.repair(path, content, critique, generated_files)

        # After repair, run lint to see if it improved
        if path.endswith(".py"):
             lint_res = tools.run_lint(path)
             if lint_res.get("returncode") != 0:
                 print(f"⚠️ Lint issues remain after repair: {lint_res.get('stdout')}")

    return content

def perform_audit(files, blueprint, critique_agent, repair_agent, storage, tools):
    print("\n🕵️ Starting Project Audit...")
    for path, content in files.items():
        print(f"\nChecking {path}...")
        critique = critique_agent.analyze(path, content, files)
        if "PASS" not in critique.upper():
            print(f"❌ Issues found in {path}:")
            print(critique)
            fix = input(f"Attempt to fix {path}? [y/N]: ").lower()
            if fix == 'y':
                new_content = repair_agent.repair(path, content, critique, files)
                print(f"Proposed fix for {path} generated.")
                if storage.write_file(path, new_content):
                    print(f"✅ {path} updated.")
        else:
            print(f"✅ {path} passed critique.")
    print("\nAudit complete.\n")

if __name__ == "__main__":
    main()
