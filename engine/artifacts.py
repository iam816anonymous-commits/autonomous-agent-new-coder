import os
import json
from typing import List, Optional

class ArtifactManager:
    """
    Safely manages task artifacts under a configured artifact root directory.
    Enforces path traversal safety using commonpath to prevent escaping the artifact root.
    """
    def __init__(self, artifact_root: Optional[str] = None):
        if artifact_root is None:
            artifact_root = os.path.join(os.getcwd(), "artifacts")
        self.artifact_root = os.path.realpath(os.path.abspath(artifact_root))
        os.makedirs(self.artifact_root, exist_ok=True)

    def _sanitize_path_segment(self, segment: str) -> str:
        if ".." in segment or segment.startswith("/") or "\\" in segment:
            raise ValueError(f"Path traversal attempted in artifact segment: {segment}")
        return segment

    def get_task_artifact_dir(self, task_id: str) -> str:
        clean_task_id = self._sanitize_path_segment(task_id)
        target_dir = os.path.realpath(os.path.abspath(os.path.join(self.artifact_root, clean_task_id)))

        try:
            if os.path.commonpath([self.artifact_root, target_dir]) != self.artifact_root or target_dir == self.artifact_root:
                raise ValueError(f"Artifact path traversal blocked for task_id: {task_id}")
        except ValueError:
            raise ValueError(f"Artifact path traversal blocked for task_id: {task_id}")

        os.makedirs(target_dir, exist_ok=True)
        return target_dir

    def write_artifact(self, task_id: str, filename: str, content: str) -> str:
        task_dir = self.get_task_artifact_dir(task_id)
        clean_filename = self._sanitize_path_segment(filename)
        file_path = os.path.realpath(os.path.abspath(os.path.join(task_dir, clean_filename)))

        try:
            if os.path.commonpath([task_dir, file_path]) != task_dir:
                raise ValueError(f"Artifact path traversal blocked for filename: {filename}")
        except ValueError:
            raise ValueError(f"Artifact path traversal blocked for filename: {filename}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return file_path

    def read_artifact(self, task_id: str, filename: str) -> Optional[str]:
        task_dir = self.get_task_artifact_dir(task_id)
        clean_filename = self._sanitize_path_segment(filename)
        file_path = os.path.realpath(os.path.abspath(os.path.join(task_dir, clean_filename)))

        try:
            if os.path.commonpath([task_dir, file_path]) != task_dir or not os.path.exists(file_path):
                return None
        except ValueError:
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def list_artifacts(self, task_id: str) -> List[str]:
        task_dir = self.get_task_artifact_dir(task_id)
        if not os.path.exists(task_dir):
            return []
        return sorted(os.listdir(task_dir))
