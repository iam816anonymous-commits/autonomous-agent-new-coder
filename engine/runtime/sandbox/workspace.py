import os
import shutil
import tempfile
from typing import Optional
from .errors import WorkspaceEscapeError

class WorkspaceManager:
    """
    Manages isolated execution workspace creation, boundary enforcement, and safe copying.
    """
    @classmethod
    def validate_boundary(cls, workspace_root: str, target_path: str) -> str:
        real_root = os.path.realpath(workspace_root)
        real_target = os.path.realpath(target_path)
        try:
            common = os.path.commonpath([real_root, real_target])
        except ValueError:
            raise WorkspaceEscapeError(f"Path escape attempt: '{target_path}' is outside workspace '{workspace_root}'.")

        if common != real_root:
            raise WorkspaceEscapeError(f"Path escape attempt: '{target_path}' escapes workspace root '{workspace_root}'.")
        return real_target

    @classmethod
    def validate_symlink_target(cls, workspace_root: str, symlink_path: str) -> None:
        real_root = os.path.realpath(workspace_root)
        if os.path.islink(symlink_path):
            target = os.readlink(symlink_path)
            if os.path.isabs(target):
                resolved = os.path.realpath(target)
            else:
                resolved = os.path.realpath(os.path.join(os.path.dirname(symlink_path), target))

            try:
                common = os.path.commonpath([real_root, resolved])
                if common != real_root:
                    raise WorkspaceEscapeError(f"Symlink escape attempt: '{symlink_path}' points to '{resolved}' outside workspace.")
            except ValueError:
                raise WorkspaceEscapeError(f"Symlink escape attempt: '{symlink_path}' points outside workspace.")

    @classmethod
    def create_isolated_copy(cls, source_workspace: str, temp_dir: Optional[str] = None) -> str:
        real_source = os.path.realpath(source_workspace)
        dest_dir = tempfile.mkdtemp(prefix="jules_sandbox_ws_", dir=temp_dir)
        real_dest = os.path.realpath(dest_dir)

        for root, dirs, files in os.walk(real_source, followlinks=False):
            rel_root = os.path.relpath(root, real_source)
            target_root = os.path.join(real_dest, rel_root) if rel_root != "." else real_dest

            os.makedirs(target_root, exist_ok=True)

            for d in dirs:
                dir_path = os.path.join(root, d)
                if os.path.islink(dir_path):
                    cls.validate_symlink_target(real_source, dir_path)

            for f in files:
                src_file = os.path.join(root, f)
                dst_file = os.path.join(target_root, f)

                if os.path.islink(src_file):
                    cls.validate_symlink_target(real_source, src_file)
                    target = os.readlink(src_file)
                    os.symlink(target, dst_file)
                else:
                    shutil.copy2(src_file, dst_file)

        return real_dest

    @classmethod
    def cleanup_workspace(cls, workspace_path: str) -> bool:
        try:
            if os.path.exists(workspace_path):
                shutil.rmtree(workspace_path)
            return True
        except Exception:
            return False
