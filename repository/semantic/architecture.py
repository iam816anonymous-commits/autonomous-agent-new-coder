import os
from typing import Dict, Any, List, Set, Optional
from .models import ArchitecturePattern, ConfidenceLevel
from repository.models import RepositoryInfo

class ArchitectureDetector:
    """
    Deterministically detects architectural boundaries (layered, MVC, API/controller, service/repository) with evidence.
    """
    @classmethod
    def detect_architecture(cls, repo_info: RepositoryInfo) -> Dict[str, Any]:
        source_paths = [p.lower() for p in repo_info.source_files]
        evidence = []
        patterns = []

        # Layered / MVC / Service-Repo checks
        has_controllers = any("controller" in p or "routes" in p or "api" in p for p in source_paths)
        has_services = any("service" in p or "domain" in p for p in source_paths)
        has_repos = any("repository" in p or "db" in p or "store" in p or "models" in p for p in source_paths)

        if has_controllers and has_services and has_repos:
            patterns.append(ArchitecturePattern.SERVICE_REPOSITORY.value)
            patterns.append(ArchitecturePattern.LAYERED.value)
            evidence.append("Found controller/route, service, and repository/model path conventions.")

        elif has_controllers:
            patterns.append(ArchitecturePattern.API_CONTROLLER.value)
            evidence.append("Found API/controller/route path conventions.")

        confidence = ConfidenceLevel.HIGH if len(patterns) >= 2 else (ConfidenceLevel.MEDIUM if len(patterns) == 1 else ConfidenceLevel.UNKNOWN)

        return {
            "patterns": patterns if patterns else [ArchitecturePattern.UNKNOWN.value],
            "confidence": confidence.value,
            "evidence": evidence
        }
