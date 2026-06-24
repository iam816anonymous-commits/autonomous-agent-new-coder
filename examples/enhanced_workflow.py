import os
import sys
from unittest.mock import MagicMock

# Project root setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_creator.core.manifest import ProjectManifest
from project_creator.core.orchestrator import Orchestrator
from project_creator.core.session import SessionManager
from project_creator.core.storage import Storage
from project_creator.core.tools import ToolExecutor


def run_enhanced_demo():
    print("\n" + "=" * 60)
    print("🚀 MINI JULES ENHANCED WORKFLOW DEMO")
    print("=" * 60 + "\n")

    # Setup
    router = MagicMock()
    # Mocking a JSON requirements summary
    router.generate.return_value = '{"objective": "demo", "tech_stack": "mocked"}'

    storage = Storage("enhanced_demo")
    tools = ToolExecutor("enhanced_demo")
    manifest = ProjectManifest("enhanced_demo")
    session = SessionManager("enhanced_demo")

    agents = {
        "planner": MagicMock(),
        "coder": MagicMock(),
        "critique": MagicMock(),
        "repair": MagicMock(),
    }

    orch = Orchestrator(router, agents, storage, tools, manifest, session)

    # Demo 1: Dialogue System
    print("--- Demo 1: Dialogue System ---")
    # Simulate user inputs for the demo
    sys.stdin = open(os.devnull, "r")  # Prevents hanging on input()
    try:
        reqs = orch.gather_requirements("Build a task manager")
        print(f"Extracted Requirements: {reqs}\n")
    except EOFError:
        print("Requirements gathering skipped (non-interactive).\n")

    # Demo 2: Dependency Analysis
    print("--- Demo 2: Dependency Analysis ---")
    blueprint = {
        "files": [
            {"path": "models.py", "description": "Core data models"},
            {"path": "database.py", "description": "Uses models to save data"},
            {"path": "main.py", "description": "Entry point using database and models"},
        ]
    }
    orch.blueprint = blueprint
    orch.dependency_analyzer.analyze_project(blueprint["files"])
    order = orch.dependency_analyzer.get_dependency_order()
    print(f"Topological Sort for Generation: {' -> '.join(order)}\n")

    # Demo 3: Error Classification
    print("--- Demo 3: Error Classification ---")
    err_msg = "ModuleNotFoundError: No module named 'fastapi'"
    cat, sev = orch.error_classifier.classify_error(err_msg)
    plan = orch.error_classifier.get_repair_plan(cat)
    print(f"Error: {err_msg}")
    print(f"Category: {cat.value}, Severity: {sev.name}")
    print(f"Plan: {plan}\n")

    # Demo 4: Test Detection
    print("--- Demo 4: Test Detection ---")
    fw = orch.test_executor.detect_test_framework()
    print(f"Detected Test Framework: {fw}\n")

    print("=" * 60)
    print("✅ DEMO COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_enhanced_demo()
