import os
import json
import sys

# Ensure the parent directory is in sys.path so we can import 'core'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from core.generator import Generator
    from core.storage import Storage
except ImportError:
    # Fallback for different execution contexts
    from .core.generator import Generator
    from .core.storage import Storage

def main():
    print("\n" + "="*50)
    print("🚀 Welcome to the Multi-File Project Creator!")
    print("="*50 + "\n")

    try:
        generator = Generator()
    except Exception as e:
        print(f"❌ Failed to initialize Gemini Client: {e}")
        sys.exit(1)

    project_dir = input("Enter the project directory name (default: 'generated_project'): ").strip() or "generated_project"
    storage = Storage(project_dir)

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
        user_prompt = input("What would you like to build? Describe your project:\n> ")

        # Check if project_dir exists and read files if it does
        existing_context = storage.read_existing_files()
        if existing_context:
            print(f"🔍 Found {len(existing_context)} existing files in '{project_dir}'. Using them as context.")

        print("\n🏗️  Generating project blueprint...")
        try:
            blueprint = generator.generate_blueprint(user_prompt, list(existing_context.keys()))
        except Exception as e:
            print(f"❌ Error generating blueprint: {e}")
            sys.exit(1)

        # Interactive refinement
        while True:
            print("\n" + "-"*30)
            print("📋 Proposed Project Structure:")
            print("-"*30)
            for i, file in enumerate(blueprint['files']):
                print(f"  {i+1:2d}. {file['path']} - {file['description']}")

            refine = input("\nWould you like to [A]dd/Remove files, [R]efine architecture, or [P]roceed? [A/R/P]: ").lower()
            if refine == 'p':
                break
            elif refine in ['a', 'r']:
                feedback = input("Enter your feedback: ")
                print("\n🔄 Updating blueprint...")
                try:
                    blueprint = generator.generate_blueprint(
                        f"Update the previous blueprint based on this feedback: {feedback}. Original goal: {user_prompt}",
                        blueprint
                    )
                except Exception as e:
                    print(f"❌ Error updating blueprint: {e}")
            else:
                print("Invalid option. Please choose A, R, or P.")

        generated_files.update(existing_context)

    # Code Generation Phase
    files_to_generate = blueprint['files']

    print("\n" + "="*50)
    print(f"🛠️  Assembling Project: {blueprint['project_name']}")
    print("="*50)

    for i, file_meta in enumerate(files_to_generate):
        path = file_meta['path']

        # If the file already exists in context and we are not in a "resume" that specifically needs it,
        # we might skip it or ask. For simplicity, if it's in generated_files (from existing or state), we skip.
        if path in generated_files:
            continue

        print(f"📝 Generating ({i+1}/{len(files_to_generate)}): {path}...")
        try:
            content = generator.generate_file_content(
                path,
                file_meta['description'],
                blueprint,
                generated_files
            )

            if storage.write_file(path, content):
                generated_files[path] = content
                # Save state after each successful file
                storage.save_state({
                    "blueprint": blueprint,
                    "generated_files": generated_files
                })
        except Exception as e:
            print(f"\n❌ Error generating {path}: {e}")
            print("💾 State saved. You can resume later by running the script again.")
            sys.exit(1)

    print("\n" + "="*50)
    print(f"✅ Project '{blueprint['project_name']}' successfully assembled in '{project_dir}'!")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
