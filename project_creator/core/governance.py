import os

class GovernanceLayer:
    IMMUTABLE_FILES = {
        "project_creator/core/evolution.py",
        "project_creator/core/memory.py",
        "project_creator/core/tools.py",
        "project_creator/core/storage.py",
        "project_creator/core/sandbox.py"
    }

    @staticmethod
    def is_modification_allowed(file_path):
        """Checks if the file is allowed to be modified by the agent."""
        # Normalize path
        normalized = file_path.replace("\\", "/")
        if normalized in GovernanceLayer.IMMUTABLE_FILES:
            return False
        return True

    @staticmethod
    def enforce_boundary(file_path):
        if not GovernanceLayer.is_modification_allowed(file_path):
            raise PermissionError(f"Governance Boundary Violation: Modification of '{file_path}' is restricted.")
