import os
import hashlib
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .errors import WorkspaceEscapeError

class FileChangeType(Enum):
    UNCHANGED = "UNCHANGED"
    ADDED = "ADDED"
    MODIFIED = "MODIFIED"
    DELETED = "DELETED"

@dataclass
class FileSnapshot:
    relative_path: str
    file_type: str  # "file", "directory", "symlink"
    size: int
    content_hash: Optional[str] = None

@dataclass
class WorkspaceSnapshot:
    workspace_root: str
    files: Dict[str, FileSnapshot] = field(default_factory=dict)
    summary_hash: str = ""

@dataclass
class WorkspaceChange:
    relative_path: str
    change_type: FileChangeType
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None

@dataclass
class WorkspaceDiff:
    changes: List[WorkspaceChange] = field(default_factory=list)
    has_changes: bool = False

class WorkspaceSnapshotter:
    """
    Computes streaming workspace snapshots and deterministic file diffs.
    """
    CHUNK_SIZE = 64 * 1024  # 64 KB

    @classmethod
    def compute_file_hash(cls, filepath: str) -> str:
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(cls.CHUNK_SIZE):
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def capture(cls, workspace_root: str) -> WorkspaceSnapshot:
        real_root = os.path.realpath(workspace_root)
        files: Dict[str, FileSnapshot] = {}
        summary_hasher = hashlib.sha256()

        for root, dirs, filenames in os.walk(real_root, followlinks=False):
            # Sort directories and files in place for deterministic traversal
            dirs.sort()
            filenames.sort()

            for filename in filenames:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, real_root)

                # Symlink check
                if os.path.islink(full_path):
                    target = os.readlink(full_path)
                    content_hash = hashlib.sha256(target.encode("utf-8")).hexdigest()
                    snapshot = FileSnapshot(
                        relative_path=rel_path,
                        file_type="symlink",
                        size=0,
                        content_hash=content_hash
                    )
                else:
                    try:
                        st = os.stat(full_path)
                        content_hash = cls.compute_file_hash(full_path)
                        snapshot = FileSnapshot(
                            relative_path=rel_path,
                            file_type="file",
                            size=st.st_size,
                            content_hash=content_hash
                        )
                    except (PermissionError, FileNotFoundError):
                        continue

                files[rel_path] = snapshot
                summary_hasher.update(f"{rel_path}:{snapshot.content_hash}".encode("utf-8"))

        summary_hash = summary_hasher.hexdigest()
        return WorkspaceSnapshot(workspace_root=real_root, files=files, summary_hash=summary_hash)

    @classmethod
    def diff(cls, before: WorkspaceSnapshot, after: WorkspaceSnapshot) -> WorkspaceDiff:
        changes: List[WorkspaceChange] = []
        all_paths = sorted(set(before.files.keys()) | set(after.files.keys()))

        for path in all_paths:
            in_before = path in before.files
            in_after = path in after.files

            if in_before and not in_after:
                changes.append(WorkspaceChange(
                    relative_path=path,
                    change_type=FileChangeType.DELETED,
                    old_hash=before.files[path].content_hash,
                    new_hash=None
                ))
            elif not in_before and in_after:
                changes.append(WorkspaceChange(
                    relative_path=path,
                    change_type=FileChangeType.ADDED,
                    old_hash=None,
                    new_hash=after.files[path].content_hash
                ))
            else:
                old_h = before.files[path].content_hash
                new_h = after.files[path].content_hash
                if old_h != new_h:
                    changes.append(WorkspaceChange(
                        relative_path=path,
                        change_type=FileChangeType.MODIFIED,
                        old_hash=old_h,
                        new_hash=new_h
                    ))

        return WorkspaceDiff(changes=changes, has_changes=len(changes) > 0)
