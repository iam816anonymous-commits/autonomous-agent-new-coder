import ast
import os
import re

from project_creator.memory.vector_store import VectorStore

from .constitution import LearningConstitution
from .event_bus import bus
from .memory_db import CodingMemory


class PatternLearner:
    def __init__(self, db_path):
        self.memory = CodingMemory(db_path)
        # P2-9: Consolidate vector stores into a single main index
        index_path = os.path.join(os.path.dirname(db_path), "jules_vectors.idx")
        self.vector_store = VectorStore(index_path)
        self._setup_subscriptions()

    def _setup_subscriptions(self):
        bus.subscribe("PATCH_ACCEPTED", self.learn_from_patch)
        bus.subscribe("FILE_OPEN", self.learn_from_file)
        bus.subscribe("MANUAL_EDIT_DETECTED", self.learn_from_edit)
        self.current_source = "SELF"

    def learn_from_edit(self, data):
        # Learn from what the user changed Jules' code into
        path = data.get("path")
        user_code = data.get("user_code", "")
        if user_code:
            print(f"🧠 PatternLearner: Learning from manual user edit in {path}")
            self._extract_patterns(user_code, source_type="USER")
            self.memory.add_snippet(path, user_code, "MANUAL_EDIT", source_type="USER")

    def learn_from_patch(self, data):
        # Learn from code that was actually accepted
        content = data.get("content", "")
        self._extract_patterns(content, source_type="USER")
        self.memory.add_snippet(
            data.get("path"), content, "ACCEPTED", source_type="USER"
        )

    def learn_from_file(self, data):
        # Learn from existing codebase style
        content = data.get("content", "")
        path = data.get("path", "")
        source = getattr(self, "current_source", "SELF")
        self._extract_patterns(content, source_type=source)
        # Also index existing files semantically
        self.vector_store.add(content, {"path": path, "type": "existing_code"})

    def _extract_patterns(self, content, source_type="SELF"):
        if not content:
            return

        # Apply Constitution Scrubbing before learning
        content = LearningConstitution.scrub(content)

        # 1. Extract Imports
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.memory.learn_pattern(
                            "import", alias.name, source_type=source_type
                        )
                elif isinstance(node, ast.ImportFrom):
                    self.memory.learn_pattern(
                        "import", node.module, source_type=source_type
                    )
        except:
            pass

        # 2. Extract specific API patterns (e.g. FastAPI, Streamlit)
        if "APIRouter()" in content:
            self.memory.learn_pattern(
                "api_style", "fastapi_router", source_type=source_type
            )
        if "app = FastAPI()" in content:
            self.memory.learn_pattern(
                "api_style", "fastapi_app", source_type=source_type
            )
        if "import streamlit as st" in content or "import streamlit" in content:
            self.memory.learn_pattern(
                "api_style", "streamlit_app", source_type=source_type
            )

        # 3. Naming Conventions (Heuristic)
        if re.search(r"def [a-z_]+", content):
            self.memory.learn_pattern("naming", "snake_case", source_type=source_type)
        elif re.search(r"def [a-z][A-Z]", content):
            self.memory.learn_pattern("naming", "camelCase", source_type=source_type)

        # 4. Project Idioms (AST-based)
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                # Detect Decorators (e.g., @app.get, @pytest.fixture)
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Call):
                            func = dec.func
                        else:
                            func = dec

                        # Flatten attribute access (e.g. app.get)
                        parts = []
                        while isinstance(func, ast.Attribute):
                            parts.append(func.attr)
                            func = func.value
                        if isinstance(func, ast.Name):
                            parts.append(func.id)

                        if parts:
                            idiom = ".".join(reversed(parts))
                            self.memory.learn_pattern(
                                "idiom", f"decorator:{idiom}", source_type=source_type
                            )

                # Detect Base Classes
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            self.memory.learn_pattern(
                                "idiom",
                                f"base_class:{base.id}",
                                source_type=source_type,
                            )
        except:
            pass
