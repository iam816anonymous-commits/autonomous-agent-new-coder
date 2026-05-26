import os
import sys
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

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
        self.session = None
        self.blueprint = None
        self.generated_files = {}

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

@app.post("/initialize")
async def initialize_project(goal: str = Body(...), project_name: str = Body(...)):
    state.storage = Storage(project_name)
    state.tools = ToolExecutor(project_name)
    state.manifest = ProjectManifest(state.storage.project_root)
    state.session = SessionManager(state.storage.project_root)
    state.manifest.create(goal, "python-v1", [])
    return {"status": "initialized", "id": project_name}

@app.post("/plan")
async def plan_project(goal: str = Body(...)):
    state.blueprint = state.planner.create_blueprint(goal)
    state.manifest.update_field("files", [f['path'] for f in state.blueprint['files']])
    state.session.save_session(state.blueprint, state.generated_files, [], [])
    return state.blueprint

@app.post("/apply")
async def apply_file(path: str = Body(...), content: str = Body(...)):
    if state.storage.write_file(path, content, interactive=False):
        state.generated_files[path] = content
        state.manifest.add_approval(path)
        state.session.save_session(state.blueprint, state.generated_files, [], [p for p in state.generated_files])
        return {"status": "success"}
    return {"status": "error"}

@app.get("/manifest")
async def get_manifest():
    if not state.manifest: return {}
    return state.manifest.load()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
