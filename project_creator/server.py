import os
import sys
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict

# Ensure project_root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_creator.core.storage import Storage
from project_creator.core.tools import ToolExecutor
from project_creator.core.manifest import ProjectManifest
from project_creator.router.provider_router import ProviderRouter
from project_creator.agents.planner_agent import PlannerAgent
from project_creator.agents.coder_agent import CoderAgent
from project_creator.agents.critique_agent import CritiqueAgent
from project_creator.agents.repair_agent import RepairAgent

app = FastAPI()

class SessionState:
    def __init__(self):
        self._router = None
        self._planner = None
        self._coder = None
        self._critique_agent = None
        self._repair_agent = None
        self.storage = None
        self.tools = None
        self.manifest = None
        self.blueprint = None
        self.generated_files = {}
        self.patches = []

    @property
    def router(self):
        if not self._router: self._router = ProviderRouter()
        return self._router
    @property
    def planner(self):
        if not self._planner: self._planner = PlannerAgent(self.router)
        return self._planner
    @property
    def coder(self):
        if not self._coder: self._coder = CoderAgent(self.router)
        return self._coder
    @property
    def critique_agent(self):
        if not self._critique_agent: self._critique_agent = CritiqueAgent(self.router)
        return self._critique_agent
    @property
    def repair_agent(self):
        if not self._repair_agent: self._repair_agent = RepairAgent(self.router)
        return self._repair_agent

state = SessionState()

class GoalRequest(BaseModel):
    goal: str
    project_name: str

@app.post("/initialize")
async def initialize_project(req: GoalRequest):
    state.storage = Storage(req.project_name)
    state.tools = ToolExecutor(req.project_name)
    state.manifest = ProjectManifest(state.storage.project_root)
    return {"status": "initialized", "path": state.storage.project_root}

@app.post("/plan")
async def generate_blueprint(req: GoalRequest):
    state.blueprint = state.planner.create_blueprint(req.goal)
    state.manifest.create(req.goal, "python-vscode", [f['path'] for f in state.blueprint['files']])
    return state.blueprint

@app.get("/manifest")
async def get_manifest():
    if not state.manifest: return {"error": "no project"}
    return state.manifest.load()

# --- Workspace Agent Endpoints ---

@app.get("/workspace/scan")
async def scan_workspace():
    if not state.storage: return {}
    return state.storage.read_existing_files()

@app.post("/workspace/read")
async def read_files(paths: List[str]):
    results = {}
    for p in paths:
        try:
            full_path = state.storage._safe_join(p)
            with open(full_path, 'r') as f:
                results[p] = f.read()
        except: pass
    return results

@app.get("/workspace/git_status")
async def get_git_status():
    if not state.tools: return {"error": "no tools"}
    # The ToolExecutor now has a whitelist, so we use it
    return state.tools.execute("git status")

# --- Generation & Patching ---

@app.post("/generate_file")
async def generate_file(path: str, description: str):
    content = state.coder.generate_file(path, description, state.blueprint, state.generated_files)
    return {"path": path, "content": content}

@app.post("/propose_patch")
async def propose_patch(path: str, content: str):
    critique = state.critique_agent.analyze(path, content, state.blueprint, state.generated_files)
    patch = state.repair_agent.propose_patch(path, content, critique, state.blueprint, state.generated_files)
    if patch:
        state.patches.append(patch)
    return patch

@app.post("/apply_patch")
async def apply_patch(path: str, content: str):
    if state.storage.write_file(path, content):
        state.generated_files[path] = content
        state.manifest.add_approval(path)
        return {"status": "success"}
    return {"status": "failed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
