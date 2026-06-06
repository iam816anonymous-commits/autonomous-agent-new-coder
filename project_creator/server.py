import os
import sys
from fastapi import FastAPI, HTTPException, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import re
import asyncio

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
        self.monitor = None

    @property
    def router(self):
        if not self._router: self._router = ProviderRouter()
        return self._router

    def init_project(self, name, goal, plan=True):
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
        if plan:
            return self.orch.plan(goal)
        return {"status": "initialized", "project": name}

state = GlobalState()

@app.post("/initialize")
async def initialize(goal: str = Body(...), project_name: str = Body(...)):
    return state.init_project(project_name, goal, plan=False)

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

@app.post("/verify")
async def verify():
    if not state.orch: raise HTTPException(400, "Not initialized")
    success = state.orch.run_tests_with_repair()
    return {"status": "verified" if success else "failed", "success": success}

@app.get("/manifest")
async def get_manifest():
    if not state.orch: return {}
    return state.orch.manifest.load()

@app.post("/events")
async def receive_event(event: Dict[str, Any]):
    collector.collect(event.get("type", "UNKNOWN"), event.get("data", {}))
    return {"status": "ok"}

@app.get("/learning/recent")
async def get_recent_activity(limit: int = 5):
    from project_creator.learning import DB_PATH
    import sqlite3
    try:
        if not os.path.exists(DB_PATH):
            return []
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            # Fetch from snippets (edits/patches) and patterns
            cursor.execute("SELECT 'PATTERN' as type, pattern_type as label, content, last_seen as ts FROM patterns ORDER BY last_seen DESC LIMIT ?", (limit,))
            patterns = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT 'CODE' as type, status as label, file_path as content, created_at as ts FROM snippets ORDER BY created_at DESC LIMIT ?", (limit,))
            snippets = [dict(row) for row in cursor.fetchall()]

            combined = patterns + snippets
            combined.sort(key=lambda x: x['ts'], reverse=True)
            return combined[:limit]
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/learning/patterns")
async def get_patterns():
    from project_creator.learning import DB_PATH
    import sqlite3
    try:
        if not os.path.exists(DB_PATH):
            return []
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patterns ORDER BY frequency DESC")
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/learning/scan")
async def trigger_scan(path: str = Body(default=".", embed=True)):
    from project_creator.learning import initialize_reality_learning
    try:
        repo, commit, monitor = initialize_reality_learning(path)
        state.monitor = monitor
        monitor.start() # Use watchdog instead of polling loop
        return {"status": "scan_started"}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.put("/learning/patterns/{pattern_id}")
async def update_pattern(pattern_id: int, content: str = Body(..., embed=True)):
    from project_creator.learning import DB_PATH
    import sqlite3
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE patterns SET content = ? WHERE id = ?", (content, pattern_id))
            conn.commit()
            return {"status": "ok"}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.delete("/learning/patterns/{pattern_id}")
async def delete_pattern(pattern_id: int):
    from project_creator.learning import DB_PATH
    import sqlite3
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM patterns WHERE id = ?", (pattern_id,))
            conn.commit()
            return {"status": "ok"}
    except Exception as e:
        raise HTTPException(500, str(e))

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

@app.post("/learning/export")
async def export_lora(output_path: str = Body(default="lora_dataset.jsonl", embed=True)):
    from project_creator.exports.lora_dataset import DatasetExporter
    from project_creator.learning import DB_PATH
    try:
        exporter = DatasetExporter(DB_PATH)
        count = exporter.export_lora_jsonl(output_path)
        return {"status": "ok", "count": count, "path": output_path}
    except Exception as e:
        raise HTTPException(500, str(e))

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
