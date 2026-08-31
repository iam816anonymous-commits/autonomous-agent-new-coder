import re
from typing import Dict, Any, Optional, Tuple

class ParameterExtractor:
    """
    Deterministic parameter extractor using rule-based regular expressions.
    """

    @staticmethod
    def extract_symbol_rename(text: str) -> Optional[Dict[str, str]]:
        # "Rename foo to bar", "Change function foo to bar", "Rename class Foo to Bar"
        pattern = re.compile(
            r'\b(?:rename|change)\s+(?:function\s+|class\s+|method\s+|symbol\s+|variable\s+)?([a-zA-Z0-9_$]+)\s+to\s+([a-zA-Z0-9_$]+)\b',
            re.IGNORECASE
        )
        match = pattern.search(text)
        if match:
            return {"old_name": match.group(1), "new_name": match.group(2)}
        return None

    @staticmethod
    def extract_dependency_upgrade(text: str) -> Optional[Dict[str, str]]:
        # "Upgrade FastAPI to 0.120", "Update React to version 19"
        pattern = re.compile(
            r'\b(?:upgrade|update)\s+([a-zA-Z0-9_$-]+)(?:\s+(?:to\s+version|\s*to|version)\s+([0-9a-zA-Z._-]+))?\b',
            re.IGNORECASE
        )
        match = pattern.search(text)
        if match:
            pkg = match.group(1)
            ver = match.group(2) or "latest"
            return {"package": pkg, "target_version": ver}
        return None

    @staticmethod
    def extract_dependency_change(text: str) -> Optional[Dict[str, str]]:
        # "Replace requests with httpx"
        pattern_replace = re.compile(r'\breplace\s+([a-zA-Z0-9_$-]+)\s+with\s+([a-zA-Z0-9_$-]+)\b', re.IGNORECASE)
        m_replace = pattern_replace.search(text)
        if m_replace:
            return {"operation": "replace", "package": m_replace.group(1), "replacement": m_replace.group(2)}

        # "Add axios", "Install lodash"
        pattern_add = re.compile(r'\b(?:add|install)\s+(?:package\s+|dependency\s+)?([a-zA-Z0-9_$-]+)\b', re.IGNORECASE)
        m_add = pattern_add.search(text)
        if m_add and m_add.group(1).lower() not in {"crud", "route", "test", "tests", "documentation", "doc", "docs"}:
            return {"operation": "add", "package": m_add.group(1)}

        # "Remove lodash", "Uninstall axios"
        pattern_remove = re.compile(r'\b(?:remove|uninstall)\s+(?:package\s+|dependency\s+)?([a-zA-Z0-9_$-]+)\b', re.IGNORECASE)
        m_remove = pattern_remove.search(text)
        if m_remove:
            return {"operation": "remove", "package": m_remove.group(1)}

        return None

    @staticmethod
    def extract_file_move(text: str) -> Optional[Dict[str, str]]:
        # "Move src/foo.py to src/utils/foo.py"
        pattern = re.compile(r'\b(?:move|relocate)\s+([a-zA-Z0-9_./-]+)\s+to\s+([a-zA-Z0-9_./-]+)\b', re.IGNORECASE)
        match = pattern.search(text)
        if match:
            return {"source": match.group(1), "destination": match.group(2)}
        return None

    @staticmethod
    def extract_file_rename(text: str) -> Optional[Dict[str, str]]:
        # "Rename file foo.py to bar.py"
        pattern = re.compile(r'\brename\s+file\s+([a-zA-Z0-9_./-]+\.[a-zA-Z0-9]+)\s+to\s+([a-zA-Z0-9_./-]+\.[a-zA-Z0-9]+)\b', re.IGNORECASE)
        match = pattern.search(text)
        if match:
            return {"source": match.group(1), "destination": match.group(2)}
        return None

    @staticmethod
    def extract_route(text: str) -> Optional[Dict[str, str]]:
        # "Add GET /users/:id", "Create POST /orders", "Add DELETE endpoint for /products/:id"
        pattern = re.compile(
            r'\b(?:add|create|register)\s+(?:route\s+|endpoint\s+)?(GET|POST|PUT|DELETE|PATCH)\s+([/a-zA-Z0-9_:-]+)\b',
            re.IGNORECASE
        )
        match = pattern.search(text)
        if match:
            method = match.group(1).upper()
            route_path = match.group(2)
            parts = [p for p in route_path.split('/') if p and not p.startswith(':')]
            resource = parts[0] if parts else "unknown"
            return {"http_method": method, "route": route_path, "resource": resource}
        return None

    @staticmethod
    def extract_crud(text: str) -> Optional[Dict[str, str]]:
        # "Add CRUD for products", "Add create/read/update/delete for users"
        pattern = re.compile(r'\bcrud\s+(?:for\s+|on\s+)?([a-zA-Z0-9_$-]+)\b', re.IGNORECASE)
        match = pattern.search(text)
        if match:
            return {"resource": match.group(1)}

        pattern_full = re.compile(r'\b(?:create/read/update/delete|crud)\s+(?:operations\s+)?(?:for\s+)?([a-zA-Z0-9_$-]+)\b', re.IGNORECASE)
        m_full = pattern_full.search(text)
        if m_full:
            return {"resource": m_full.group(1)}

        return None

    @staticmethod
    def extract_migration(text: str) -> Optional[Dict[str, str]]:
        # "Convert CommonJS to ESM", "Migrate Angular version 12 to 13"
        pattern = re.compile(r'\b(?:convert|migrate)\s+([a-zA-Z0-9_$-]+)\s+to\s+([a-zA-Z0-9_$-]+)\b', re.IGNORECASE)
        match = pattern.search(text)
        if match:
            return {"from_framework": match.group(1), "to_framework": match.group(2)}
        return None
