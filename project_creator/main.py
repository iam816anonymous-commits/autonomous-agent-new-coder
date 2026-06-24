import os
import sys

# Project root setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_creator.agents.coder_agent import CoderAgent
from project_creator.agents.critique_agent import CritiqueAgent
from project_creator.agents.planner_agent import PlannerAgent
from project_creator.agents.repair_agent import RepairAgent
from project_creator.brain.repository_brain import RepositoryBrain
from project_creator.core.manifest import ProjectManifest
from project_creator.core.orchestrator import Orchestrator
from project_creator.core.session import SessionManager
from project_creator.core.storage import Storage
from project_creator.core.tools import ToolExecutor
from project_creator.learning import DB_PATH, initialize_reality_learning
from project_creator.router.provider_router import ProviderRouter


def main():
    print("\n" + "=" * 50)
    print("🤖 Unified Mini Jules Project Agent")
    print("=" * 50 + "\n")

    # --- SELF-LEARNING BOOTSTRAP ---
    print("🧠 Bootstrapping Reality Learning (Ingesting current workspace)...")
    initialize_reality_learning(".")
    brain = RepositoryBrain(DB_PATH)
    brain.ingest_repository(".")
    print("✅ Self-Learning complete. I now remember how I am built.\n")

    router = ProviderRouter()
    name = input("Project Name: ") or "jules_unified"
    goal = input("Build Goal: ")

    storage = Storage(name)
    tools = ToolExecutor(name)
    manifest = ProjectManifest(storage.project_root)
    session = SessionManager(storage.project_root)

    agents = {
        "planner": PlannerAgent(router),
        "coder": CoderAgent(router),
        "critique": CritiqueAgent(router),
        "repair": RepairAgent(router),
    }

    orch = Orchestrator(router, agents, storage, tools, manifest, session)
    blueprint = orch.plan(goal)

    if not blueprint:
        print("❌ Architecture failure.")
        return

    print("\n🏗️  Blueprint ready. Starting hierarchical generation...")

    stages = blueprint.get("stages", [])
    if not stages:
        # Fallback for old flat blueprints
        stages = [{"name": "Single Phase", "files": blueprint.get("files", [])}]

    for stage in stages:
        print(f"\n🚀 STAGE: {stage['name']}")
        for f in stage["files"]:
            res = orch.generate_and_validate(f)

            print(f"\n--- Review: {f['path']} ---")
            print(res["content"][:400] + "...")
            if input("\nApprove and Write? [y/N]: ").lower() == "y":
                orch.apply(f["path"], res["content"])
                print(f"✅ {f['path']} applied.")

    orch.manifest.update_field("status", "complete")
    print("\n🚀 Project generated successfully!")


if __name__ == "__main__":
    main()
