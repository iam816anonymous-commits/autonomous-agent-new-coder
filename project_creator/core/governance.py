import os

class GovernanceLayer:
    IMMUTABLE_FILES = {
        "project_creator/core/evolution.py",
        "project_creator/core/memory.py",
        "project_creator/core/tools.py",
        "project_creator/core/storage.py",
        "project_creator/core/sandbox.py",
        "project_creator/core/governance.py"
    }

    @staticmethod
    def is_modification_allowed(file_path):
        normalized = file_path.replace("\\", "/")
        return normalized not in GovernanceLayer.IMMUTABLE_FILES

    @staticmethod
    def enforce_boundary(file_path):
        if not GovernanceLayer.is_modification_allowed(file_path):
            raise PermissionError(f"Constitution Violation: Access to '{file_path}' is restricted.")

class GovernanceSimulator:
    @staticmethod
    def simulate_promotion(candidate_metrics, champ_metrics):
        """Checks for governance violations before promotion."""
        violations = []

        # Check 1: Cost spike
        if candidate_metrics.get('cost', 0) > champ_metrics.get('cost', 0) * 2.0:
            violations.append("Critical Cost Spike Detected (>100% increase)")

        # Check 2: Performance regression
        if candidate_metrics.get('latency', 0) > champ_metrics.get('latency', 0) * 1.5:
            violations.append("Critical Latency Drift Detected (>50% regression)")

        # Check 3: Integrity check
        if candidate_metrics.get('tests_passed', 0) < champ_metrics.get('tests_passed', 0):
             violations.append("Integrity Violation: Quality regression detected")

        return violations
