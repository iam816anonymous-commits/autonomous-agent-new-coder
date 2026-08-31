"""
Deterministic Task Classifier package for Mini-Jules.
Classifies requests and extracts engineering parameters offline without LLM dependencies.
"""

from .models import (
    TaskType,
    TaskClassificationStatus,
    TaskClassification
)

__all__ = [
    "TaskType",
    "TaskClassificationStatus",
    "TaskClassification"
]
