import os
import sys
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import re

# Project root setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from project_creator.core.storage import Storage
from project_creator.core.tools import ToolExecutor
from project_creator.core.manifest import ProjectManifest
from project_creator.core.session import SessionManager
from project_creator.core.orchestrator import Orchestrator
from project_creator.router.provider_router import ProviderRouter
from project_creator.agents.planner_agent import PlannerAgent
from project_creator.agents.coder_agent import CoderAgent
from project_creator.agents.critique_agent import CritiqueAgent
from project_creator.agents.repair_agent import RepairAgent
from project_creator.learning.collector import collector

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GlobalState:
    def __init__(self):
        self._router = None
        self.orch = None

    @property
    def router(self):
        if not self._router: self._router = ProviderRouter()
        return self._router

    def init_project(self, name, goal):
        if not re.match(r'^[a-zA-Z0-9_\-]+$', name):
            raise HTTPException(400, "Invalid project name.")

        storage = Storage(name)
        tools = ToolExecutor(name)
        manifest = ProjectManifest(storage.project_root)
        session = SessionManager(storage.project_root)
        agents = {
            'planner': PlannerAgent(self.router),
            'coder': CoderAgent(self.router),
            'critique': CritiqueAgent(self.router),
            'repair': RepairAgent(self.router)
        }
        self.orch = Orchestrator(self.router, agents, storage, tools, manifest, session)
        return self.orch.plan(goal)

state = GlobalState()

@app.post("/start")
async def start(goal: str = Body(...), name: str = Body(...)):
    return state.init_project(name, goal)

@app.post("/process_file")
async def process_file(file: Dict[str, str]):
    if not state.orch: raise HTTPException(400, "Not initialized")
    return state.orch.generate_and_validate(file)

@app.post("/approve")
async def approve(path: str = Body(...), content: str = Body(...)):
    if not state.orch: raise HTTPException(400, "Not initialized")
    if state.orch.apply(path, content):
        return {"status": "ok"}
    return {"status": "error"}

@app.get("/manifest")
async def get_manifest():
    if not state.orch: return {}
    return state.orch.manifest.load()

@app.post("/events")
async def receive_event(event: Dict[str, Any]):
    collector.collect(event.get("type", "UNKNOWN"), event.get("data", {}))
    return {"status": "ok"}

@app.get("/learning/stats")
async def get_learning_stats():
    from project_creator.learning import DB_PATH
    import sqlite3
    try:
        if not os.path.exists(DB_PATH):
            return {"patterns": 0, "snippets": 0, "failures": 0, "commits": 0, "memory_growth": "0 KB"}

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM patterns")
            patterns = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM snippets")
            snippets = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM failures")
            failures = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM git_commits")
            commits = cursor.fetchone()[0]

            size = os.path.getsize(DB_PATH) / 1024
            return {
                "patterns": patterns,
                "snippets": snippets,
                "failures": failures,
                "commits": commits,
                "memory_growth": f"{size:.1f} KB"
            }
    except Exception as e:
        return {"error": str(e)}

@app.get("/learning/context")
async def get_active_context(path: str):
    from project_creator.memory.retriever import Retriever
    from project_creator.learning import DB_PATH
    try:
        retriever = Retriever(DB_PATH)
        semantic = retriever.vector_store.search(f"File: {path}", top_k=3)
        patterns = {
            "imports": retriever.memory.get_top_patterns('import', limit=3),
            "idioms": retriever.memory.get_top_patterns('idiom', limit=3)
        }
        return {
            "semantic": semantic,
            "patterns": patterns
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
