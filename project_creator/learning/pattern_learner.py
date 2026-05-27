import ast
import re
from .event_bus import bus
from .memory_db import CodingMemory
from .constitution import LearningConstitution

class PatternLearner:
    def __init__(self, db_path):
        self.memory = CodingMemory(db_path)
        self._setup_subscriptions()

    def _setup_subscriptions(self):
        bus.subscribe("PATCH_ACCEPTED", self.learn_from_patch)
        bus.subscribe("FILE_OPEN", self.learn_from_file)

    def learn_from_patch(self, data):
        # Learn from code that was actually accepted
        content = data.get('content', '')
        self._extract_patterns(content)
        self.memory.add_snippet(data.get('path'), content, 'ACCEPTED')

    def learn_from_file(self, data):
        # Learn from existing codebase style
        content = data.get('content', '')
        path = data.get('path', '')
        self._extract_patterns(content)
        # Also index existing files semantically
        self.vector_store.add(content, {"path": path, "type": "existing_code"})

    def _extract_patterns(self, content):
        if not content: return

        # Apply Constitution Scrubbing before learning
        content = LearningConstitution.scrub(content)

        # 1. Extract Imports
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.memory.learn_pattern('import', alias.name)
                elif isinstance(node, ast.ImportFrom):
                    self.memory.learn_pattern('import', node.module)
        except: pass

        # 2. Extract specific API patterns (e.g. FastAPI APIRouter)
        if "APIRouter()" in content:
            self.memory.learn_pattern('api_style', 'fastapi_router')
        if "app = FastAPI()" in content:
            self.memory.learn_pattern('api_style', 'fastapi_app')

        # 3. Naming Conventions (Heuristic)
        if re.search(r'def [a-z_]+', content):
            self.memory.learn_pattern('naming', 'snake_case')
        elif re.search(r'def [a-z][A-Z]', content):
            self.memory.learn_pattern('naming', 'camelCase')

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
                            self.memory.learn_pattern('idiom', f"decorator:{idiom}")

                # Detect Base Classes
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            self.memory.learn_pattern('idiom', f"base_class:{base.id}")
        except: pass
