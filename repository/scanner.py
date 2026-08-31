import os
import re
from typing import List, Dict, Set, Tuple, Optional
from .models import RepositoryInfo, FileInfo

IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "__pycache__", ".pytest_cache",
    "dist", "build", "target", "bin", "obj", ".idea", ".vscode", "coverage"
}

BINARY_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib", ".exe", ".bin",
    ".zip", ".tar", ".gz", ".7z", ".png", ".jpg", ".jpeg", ".gif",
    ".ico", ".pdf", ".db", ".sqlite", ".idx", ".faiss"
}

LANGUAGE_EXTENSIONS = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".cs": "C#"
}

CANDIDATE_ENTRY_POINTS = {
    "main.py", "app.py", "server.py", "manage.py",
    "index.js", "index.ts", "main.ts", "main.go",
    "Main.java", "Program.cs"
}

class RepositoryScanner:
    """
    Deterministic static analysis scanner for software repositories.
    Operates offline without LLMs or network access.
    """
    def __init__(self, root: str):
        self.root = os.path.realpath(os.path.abspath(root))

    def _is_safe_path(self, target_path: str) -> bool:
        """Verifies that the target path is strictly within the repository root."""
        try:
            real_target = os.path.realpath(os.path.abspath(target_path))
            return real_target.startswith(self.root) and (
                len(real_target) == len(self.root) or real_target[len(self.root)] == os.sep
            )
        except Exception:
            return False

    def _is_binary_file(self, full_path: str) -> bool:
        """Heuristic check for binary files using extension and content sampling."""
        _, ext = os.path.splitext(full_path)
        if ext.lower() in BINARY_EXTENSIONS:
            return True
        try:
            with open(full_path, "rb") as f:
                chunk = f.read(8192)
                if b"\x00" in chunk:
                    return True
        except Exception:
            return True
        return False

    def scan(self) -> Tuple[RepositoryInfo, Dict[str, FileInfo]]:
        languages_detected: Set[str] = set()
        frameworks_detected: Set[str] = set()
        package_managers_detected: Set[str] = set()
        source_files: List[str] = []
        test_files: List[str] = []
        config_files: List[str] = []
        entry_points: List[str] = []
        file_info_map: Dict[str, FileInfo] = {}

        manifest_contents: Dict[str, str] = {}

        for current_root, dirs, files in os.walk(self.root, followlinks=False):
            # Safe boundary check
            if not self._is_safe_path(current_root):
                dirs.clear()
                continue

            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

            for filename in files:
                full_path = os.path.join(current_root, filename)

                if not self._is_safe_path(full_path):
                    continue

                rel_path = os.path.relpath(full_path, self.root).replace("\\", "/")

                # Size & Binary check
                file_size = 0
                try:
                    file_size = os.path.getsize(full_path)
                except Exception:
                    pass

                is_bin = self._is_binary_file(full_path)
                _, ext = os.path.splitext(filename)
                ext_lower = ext.lower()

                lang = LANGUAGE_EXTENSIONS.get(ext_lower)
                if lang:
                    languages_detected.add(lang)

                # Entry point check
                is_entry = filename in CANDIDATE_ENTRY_POINTS

                # Test file check
                is_test = False
                rel_parts = rel_path.split("/")
                if "tests" in rel_parts or "test" in rel_parts or "src/test" in rel_path:
                    is_test = True
                elif (
                    filename.startswith("test_")
                    or filename.endswith("_test.py")
                    or filename.endswith(".test.js")
                    or filename.endswith(".test.ts")
                    or filename.endswith(".spec.js")
                    or filename.endswith(".spec.ts")
                    or filename.endswith("_test.go")
                ):
                    is_test = True

                file_info = FileInfo(
                    path=rel_path,
                    language=lang,
                    is_test=is_test,
                    is_entry_point=is_entry,
                    is_binary=is_bin,
                    file_size=file_size
                )
                file_info_map[rel_path] = file_info

                if is_bin:
                    continue

                if is_test:
                    test_files.append(rel_path)
                elif lang:
                    source_files.append(rel_path)

                if is_entry:
                    entry_points.append(rel_path)

                # Collect configuration & package manager files
                if filename in {
                    "requirements.txt", "pyproject.toml", "Pipfile", "setup.py",
                    "package.json", "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
                    "CMakeLists.txt", "Makefile", "Dockerfile", "docker-compose.yml"
                } or filename.endswith(".csproj"):
                    config_files.append(rel_path)

                    # Read manifest content for framework / dependency detection
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            manifest_contents[filename] = f.read()
                    except Exception:
                        pass

        # Package manager detection
        if "requirements.txt" in manifest_contents or "setup.py" in manifest_contents:
            package_managers_detected.add("pip")
        if "pyproject.toml" in manifest_contents:
            content = manifest_contents["pyproject.toml"]
            if "poetry" in content.lower():
                package_managers_detected.add("poetry")
            elif "uv" in content.lower():
                package_managers_detected.add("uv")
            else:
                package_managers_detected.add("pip")
        if "package.json" in manifest_contents:
            package_managers_detected.add("npm")
            if os.path.exists(os.path.join(self.root, "yarn.lock")):
                package_managers_detected.add("yarn")
            if os.path.exists(os.path.join(self.root, "pnpm-lock.yaml")):
                package_managers_detected.add("pnpm")
        if "Cargo.toml" in manifest_contents:
            package_managers_detected.add("Cargo")
        if "go.mod" in manifest_contents:
            package_managers_detected.add("Go modules")
        if "pom.xml" in manifest_contents:
            package_managers_detected.add("Maven")
        if "build.gradle" in manifest_contents:
            package_managers_detected.add("Gradle")
        if any(f.endswith(".csproj") for f in config_files):
            package_managers_detected.add("dotnet")

        # Framework detection using dependency evidence
        combined_manifests = "\n".join(manifest_contents.values()).lower()
        if "fastapi" in combined_manifests:
            frameworks_detected.add("FastAPI")
        if "flask" in combined_manifests:
            frameworks_detected.add("Flask")
        if "django" in combined_manifests:
            frameworks_detected.add("Django")
        if "react" in combined_manifests:
            frameworks_detected.add("React")
        if "angular" in combined_manifests:
            frameworks_detected.add("Angular")
        if "vue" in combined_manifests:
            frameworks_detected.add("Vue")
        if "express" in combined_manifests:
            frameworks_detected.add("Express")
        if "next" in combined_manifests:
            frameworks_detected.add("Next.js")
        if "springframework" in combined_manifests or "spring-boot" in combined_manifests:
            frameworks_detected.add("Spring")

        info = RepositoryInfo(
            root=self.root,
            languages=sorted(list(languages_detected)),
            frameworks=sorted(list(frameworks_detected)),
            package_managers=sorted(list(package_managers_detected)),
            source_files=sorted(source_files),
            test_files=sorted(test_files),
            config_files=sorted(config_files),
            entry_points=sorted(entry_points)
        )

        return info, file_info_map
