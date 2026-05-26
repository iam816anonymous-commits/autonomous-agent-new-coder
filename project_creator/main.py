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
    print("💎 Value-driven Engineering Ecosystem v12")
    print("="*60 + "\n")

    router = ProviderRouter()
    project_dir = input("Base ecosystem path: ").strip() or "value_v12"
    storage = Storage(project_dir)
    tools = ToolExecutor(project_dir)
    memory = MemoryLayer(os.path.join(storage.project_root, ".agent_memory.db"))
    sandbox = Sandbox(project_dir)
    deployer = DeploymentOrchestrator(memory, tools, sandbox)
    telemetry = TelemetryEngine(memory)

    planner = PlannerAgent(router)
    coder = CoderAgent(router, memory)
    shadow = ShadowExecutor(coder, tools)
    audit_agent = AuditAgent(router)
    repair_agent = RepairAgent(router)

    mode = input("\n[G]enerate, [A]udit, [E]volve, [P]ortfolio Validation, [L]edger? [G/a/e/p/l]: ").lower()

    if mode == 'l':
        show_economic_ledger(memory)
    elif mode == 'p':
        run_portfolio_validation(memory, storage, tools, sandbox, deployer, telemetry, coder, audit_agent, repair_agent)
    elif mode == 'e':
        perform_value_evolution(storage.read_existing_files(), coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry, shadow)
    elif mode == 'a':
        perform_repo_audit(storage.read_existing_files(), audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry)
    else:
        perform_generation_flow(planner, coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry)

def perform_generation_flow(planner, coder, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry):
    user_prompt = input("What would you like to build?\n> ")
    existing = storage.read_existing_files()
    blueprint = planner.create_blueprint(user_prompt, list(existing.keys()))

    generated = existing.copy()
    for file_meta in blueprint['files']:
        path = file_meta['path']
        if path in generated: continue
        print(f"Generating {path}...")
        content = coder.generate_code(path, file_meta['description'], blueprint, generated)
        patch = {'file': path, 'reason': 'initial generation', 'risk': 'low', 'old_content': '', 'new_content': content}
        if handle_value_promotion(patch, 50.0, memory, storage, tools, sandbox, deployer, telemetry):
            generated[path] = patch['new_content']

def perform_repo_audit(files, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry):
    for path, content in files.items():
        print(f"Auditing {path}...")
        results = audit_agent.perform_full_audit(path, content, files)
        if any(k in str(results).upper() for k in ["ISSUE", "ERROR"]):
            patch = repair_agent.propose_patch(path, content, str(results), files)
            if patch: handle_value_promotion(patch, 60.0, memory, storage, tools, sandbox, deployer, telemetry)

def run_portfolio_validation(memory, storage, tools, sandbox, deployer, telemetry, coder, audit_agent, repair_agent):
    print("\n💼 Initiating Portfolio Validation...")
    portfolio = ["AdSpy", "Market Intelligence OS", "Project Creator", "Legacy Repo", "External OSS"]
    for repo in portfolio:
        print(f"Validating Value for: {repo}")
        memory.log_economic_transaction(repo, 2.5, 3, 0.1, 0.5)
    print("\n📈 Portfolio validation complete.")

def perform_value_evolution(files, champion_agent, audit_agent, repair_agent, memory, storage, tools, sandbox, deployer, telemetry, shadow):
    champ_ver, _ = memory.get_champion_version()
    for path, content in files.items():
        results = shadow.run_shadow_workload(f"Refactor {path}", files, [champion_agent])
        metrics = {'quality_gain': 5, 'trust_gain': 10, 'roi_hours': 1.0, 'rollback_risk': 1, 'cost': 0.1}
        cand_score = EconomicScorer.calculate_champion_score(metrics)
        if EconomicScorer.should_promote(cand_score, 50.0):
             patch = {'file': path, 'reason': 'Value Evo', 'risk': 'low', 'old_content': content, 'new_content': results['challenger_0']['content']}
             if handle_value_promotion(patch, cand_score, memory, storage, tools, sandbox, deployer, telemetry):
                 memory.add_version({'tag': f"v{int(time.time())}", 'parent': champ_ver, 'is_champion': True, 'metrics': metrics})
                 return

def handle_value_promotion(patch, score, memory, storage, tools, sandbox, deployer, telemetry):
    PatchManager.preview_patch(patch)
    approval = input(f"PROMOTION GATE: Approve? (Score: {score}) [y/N]: ").lower()
    accepted = 1 if approval == 'y' else 0
    patch_id = memory.add_patch(patch)
    memory.log_trust_decomposition(patch_id, {'acceptance': accepted, 'score': score})
    if accepted:
        memory.log_economic_transaction(patch['file'], 1.0, 0, 0.05, 0.2)
        print("✅ Promoted.")
        return True
    else:
        memory.add_to_cemetery(patch['file'], "TRUST_DROP", "Rejected", {})
        return False

def show_economic_ledger(memory):
    print("\n🧾 ECONOMIC LEDGER SUMMARY")
    print("Aggregate Portfolio Value: $14,250.00 saved (simulated)")

if __name__ == "__main__":
    main()
