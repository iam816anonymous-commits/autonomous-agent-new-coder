import json
import os


class Storage:
    def __init__(self, project_root):
        # Resolve to absolute path to prevent traversal via symlinks or relative dots
        self.project_root = os.path.realpath(os.path.abspath(project_root))
        self.state_file = os.path.join(self.project_root, ".agent_state.json")

    def _safe_join(self, *paths):
        """Joins paths and ensures the result is within the project_root."""
        joined_path = os.path.join(self.project_root, *paths)
        final_path = os.path.realpath(os.path.abspath(joined_path))

        if not final_path.startswith(self.project_root):
            raise ValueError(
                f"Security Warning: Attempted to access path outside project root: {final_path}"
            )
        return final_path

    def ensure_directory(self, path):
        full_path = self._safe_join(os.path.dirname(path))
        if full_path and not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)

    def write_file(self, path, content, overwrite=True, interactive=False):
        """
        Writes content to path.
        If interactive=True, will prompt user if file exists.
        Otherwise uses overwrite parameter.
        """
        # P0-3: Wire is_safe_content into write path
        from project_creator.core.utils import is_safe_content

        if not is_safe_content(content):
            print(f"🛡️  Storage: Blocked write to {path}. Dangerous content detected.")
            return False

        full_path = self._safe_join(path)
        self.ensure_directory(path)

        if os.path.exists(full_path) and interactive:
            try:
                choice = input(
                    f"File {path} exists. [O]verwrite, [S]kip, [A]bort? "
                ).lower()
                if choice == "s":
                    return False
                if choice == "a":
                    exit(1)
            except EOFError:
                # Fallback to overwrite parameter if non-interactive
                if not overwrite:
                    return False

        if not overwrite and os.path.exists(full_path):
            return False

        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True

    def save_state(self, state):
        os.makedirs(self.project_root, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def load_state(self):
        if os.path.exists(self.state_file):
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def read_existing_files(self, exclude_meta=True):
        """Reads project files while excluding internal metadata and common ignored dirs."""
        files_context = {}
        if not os.path.exists(self.project_root):
            return files_context

        ignored_dirs = {".git", "__pycache__", "node_modules", "venv", ".venv"}
        ignored_files = (
            {".agent_state.json", ".agent_session.json", "project.yaml"}
            if exclude_meta
            else set()
        )

        for root, dirs, files in os.walk(self.project_root):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in ignored_dirs]

            for file in files:
                if file in ignored_files:
                    continue
                rel_path = os.path.relpath(os.path.join(root, file), self.project_root)
                try:
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        files_context[rel_path] = f.read()
                except:
                    pass
        return files_context
