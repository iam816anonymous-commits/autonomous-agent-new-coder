import re
from typing import List, Dict, Any, Optional
from .models import TaskType, TaskClassificationStatus, TaskClassification
from .rules import (
    ALL_RULES,
    is_negated,
    is_informational_question,
    is_vague_request,
    ClassificationRule
)
from repository.models import BlastRadiusLevel

RISK_SEVERITY_ORDER = {
    BlastRadiusLevel.LOW: 1,
    BlastRadiusLevel.MEDIUM: 2,
    BlastRadiusLevel.HIGH: 3,
    BlastRadiusLevel.CRITICAL: 4
}

class TaskClassifier:
    """
    Deterministic rule-based task classifier for Mini-Jules.
    Operates offline without LLMs or network access.
    """
    def __init__(self, rules: Optional[List[ClassificationRule]] = None):
        self.rules = sorted(rules or ALL_RULES, key=lambda r: r.priority, reverse=True)

    def classify(self, request: str, repo_snapshot=None) -> TaskClassification:
        req_clean = request.strip()

        # 1. Check for vague/generic requests
        if is_vague_request(req_clean):
            return TaskClassification(
                task_type=TaskType.AMBIGUOUS,
                status=TaskClassificationStatus.AMBIGUOUS,
                confidence=0.50,
                evidence=["Request matches generic vague phrase pattern"],
                warnings=["Generic request requiring clarification. Please specify concrete action or target."]
            )

        # 2. Check for explicit negation
        if is_negated(req_clean) and not is_informational_question(req_clean):
            return TaskClassification(
                task_type=TaskType.AMBIGUOUS,
                status=TaskClassificationStatus.AMBIGUOUS,
                confidence=0.50,
                evidence=["Explicit negation/prohibition detected in request"],
                warnings=["Request contains negative constraints prohibiting changes."]
            )

        # 3. Check for composite multi-task requests (e.g. "X and Y")
        if " and " in req_clean.lower():
            clauses = [c.strip() for c in re.split(r'\bAND\b', req_clean, flags=re.IGNORECASE) if c.strip()]
            subtasks = []
            for clause in clauses:
                sub = self._classify_single(clause, repo_snapshot)
                if sub.status == TaskClassificationStatus.SUPPORTED:
                    subtasks.append(sub)

            if len(subtasks) > 1:
                return TaskClassification(
                    task_type=TaskType.COMPOSITE_TASK,
                    status=TaskClassificationStatus.SUPPORTED,
                    confidence=min(s.confidence for s in subtasks),
                    extracted_parameters={"subtask_count": len(subtasks)},
                    evidence=[f"Identified {len(subtasks)} subtasks in composite request"],
                    required_capabilities=list(set(c for s in subtasks for c in s.required_capabilities)),
                    risk=max((s.risk for s in subtasks), key=lambda r: RISK_SEVERITY_ORDER.get(r, 1)),
                    subtasks=subtasks
                )

        # 4. Classify single request
        return self._classify_single(req_clean, repo_snapshot)

    def _classify_single(self, request: str, repo_snapshot=None) -> TaskClassification:
        matching_candidates: List[TaskClassification] = []

        for rule in self.rules:
            if rule.matches(request, repo_snapshot):
                res = rule.evaluate(request, repo_snapshot)
                matching_candidates.append(res)

        if not matching_candidates:
            return TaskClassification(
                task_type=TaskType.UNKNOWN,
                status=TaskClassificationStatus.UNSUPPORTED,
                confidence=0.0,
                evidence=["No deterministic classification rule matched the request"],
                warnings=["Unsupported or unrecognized engineering request."]
            )

        # Select highest confidence match
        best_match = max(matching_candidates, key=lambda c: (c.confidence, c.task_type.value))
        return best_match
