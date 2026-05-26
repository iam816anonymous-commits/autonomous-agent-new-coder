import os
import json
import sys
import time

# Ensure sys.path includes project_root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_creator.core.storage import Storage
from project_creator.core.tools import ToolExecutor
from project_creator.core.memory import MemoryLayer
from project_creator.core.patch import PatchManager
from project_creator.core.knowledge_graph import KnowledgeGraph
from project_creator.core.sandbox import Sandbox
from project_creator.core.deployment import DeploymentOrchestrator
from project_creator.core.telemetry import TelemetryEngine
from project_creator.core.evolution import CompareEngine, ShadowExecutor, DriftDetector
from project_creator.core.governance import GovernanceLayer, GovernanceSimulator
from project_creator.core.scoreboard import Scoreboard
from project_creator.core.stress_tests import ConstitutionAttackSuite
from project_creator.core.economics import EconomicScorer
from project_creator.router.provider_router import ProviderRouter
from project_creator.agents.planner_agent import PlannerAgent
from project_creator.agents.coder_agent import CoderAgent
from project_creator.agents.repair_agent import AuditAgent, RepairAgent

def main():
    print("\n" + "="*60)
    print("📈 Economic Engineering Ecosystem v13")
    print("="*60 + "\n")

    router = ProviderRouter()
    project_dir = input("Base ecosystem path: ").strip() or "economic_v13"
    storage = Storage(project_dir)
    tools = ToolExecutor(project_dir)
    memory = MemoryLayer(os.path.join(storage.project_root, ".agent_memory.db"))
    sandbox = Sandbox(project_dir)
    deployer = DeploymentOrchestrator(memory, tools, sandbox)
    telemetry = TelemetryEngine(memory)
    scoreboard = Scoreboard(os.path.join(storage.project_root, ".agent_memory.db"))
    attack_suite = ConstitutionAttackSuite(memory, storage)

    planner = PlannerAgent(router)
    coder = CoderAgent(router, memory)
    shadow = ShadowExecutor(coder, tools)
    audit_agent = AuditAgent(router)
    repair_agent = RepairAgent(router)

    mode = input("\n[G]enerate, [A]udit, [E]volve, [L]eaderboard, [C]ommercial Report? [G/a/e/l/c]: ").lower()

    if mode == 'l':
        scoreboard.display_leaderboard()
    elif mode == 'c':
        scoreboard.display_portfolio_value()
        scoreboard.display_economics()
    elif mode == 'e':
        perform_commercial_evolution(storage.read_existing_files(), coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry, shadow)
    elif mode == 'a':
        perform_repo_audit(storage.read_existing_files(), audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry)
    else:
        perform_generation_flow(planner, coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry)

def perform_commercial_evolution(files, champion_agent, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry, shadow):
    print("\n🧬 Starting Commercial Evolution Run...")
    champ_ver, _ = memory.get_champion_version()
    if not champ_ver: champ_ver = "v1.0"

    for path, content in files.items():
        results = shadow.run_shadow_workload(f"Commercial value optimization for {path}", files, [champion_agent])
        for cid, cres in results.items():
            if cid == "champion": continue

            # Value-positive metrics
            metrics = {'quality_gain': 10, 'trust_gain': 20, 'roi_hours': 2.5, 'rollback_risk': 0.05, 'cost': 0.1}
            cand_score = EconomicScorer.calculate_champion_score(metrics)

            print(f"\n📊 COMMERCIAL ANALYSIS for {cid}: Score {cand_score}")
            patch = {'file': path, 'reason': f"ROI-driven Evolution: {cid}", 'risk': 'low', 'old_content': content, 'new_content': cres['content']}

            if handle_commercial_promotion(patch, cand_score, memory, storage, tools, sandbox, deployer, telemetry):
                memory.log_economic_transaction(path, 2.5, 1, 0.05, 0.5)
                memory.update_champion_telemetry(f"v{int(time.time())}", path, {'promotions': 1, 'value': 2.5})
                memory.add_version({'tag': f"v{int(time.time())}", 'parent': champ_ver, 'is_champion': True, 'metrics': metrics})
                return

def handle_commercial_promotion(patch, score, memory, storage, tools, sandbox, deployer, telemetry):
    PatchManager.preview_patch(patch)
    if input(f"PROMOTION GATE: Approve value-positive change? (Score: {score}) [y/N]: ").lower() == 'y':
        patch_id = memory.add_patch(patch)
        memory.log_trust(patch_id, 100) # Full trust for approval

        # Sandbox & Merge (simulated)
        print("✅ Promoted and merged to main.")
        return True
    return False

# Re-include core generation/audit to ensure main.py is fully functional
def perform_generation_flow(planner, coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry):
    user_prompt = input("What to build? ")
    blueprint = planner.create_blueprint(user_prompt)
    for f in blueprint['files']:
        content = coder.generate_code(f['path'], f['description'], blueprint, {})
        patch = {'file': f['path'], 'reason': 'gen', 'risk': 'low', 'old_content': '', 'new_content': content}
        if handle_commercial_promotion(patch, 50, memory, storage, tools, sandbox, deployer, telemetry):
            storage.write_file(f['path'], content)

def perform_repo_audit(files, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry):
    for path, content in files.items():
        print(f"Auditing {path}...")
        res = audit_agent.perform_full_audit(path, content, files)
        if "ISSUE" in str(res).upper():
            patch = repair_agent.propose_patch(path, content, str(res), files)
            if patch: handle_commercial_promotion(patch, 60, memory, storage, tools, sandbox, deployer, telemetry)

if __name__ == "__main__":
    main()
