import os
import sqlite3

import pytest

from project_creator.learning.event_bus import bus
from project_creator.learning.memory_db import CodingMemory
from project_creator.learning.repo_learner import RepoLearner


@pytest.fixture
def test_db():
    db_path = "test_jules_memory.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    memory = CodingMemory(db_path)
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def test_workspace(tmp_path):
    d = tmp_path / "workspace"
    d.mkdir()
    (d / "test.py").write_text("import os\ndef test_func(): pass")
    (d / "sub").mkdir()
    (d / "sub" / "other.py").write_text("import sys")
    return str(d)


def test_repo_learner(test_db, test_workspace):
    # Setup pattern learner to listen
    from project_creator.learning import pattern_learner

    orig_memory = pattern_learner.memory
    pattern_learner.memory = CodingMemory(test_db)

    try:
        rl = RepoLearner(test_workspace)
        rl.scan_workspace()
    finally:
        pattern_learner.memory = orig_memory

    # Check if patterns were learned
    with sqlite3.connect(test_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM patterns WHERE pattern_type='import'")
        imports = [r[0] for r in cursor.fetchall()]
        assert "os" in imports
        assert "sys" in imports


def test_failure_logging(test_db):
    from project_creator.learning.failure_learner import FailureLearner

    fl = FailureLearner(test_db)

    bus.publish(
        "VALIDATION_FAILED",
        {
            "path": "bad.py",
            "type": "SANDBOX",
            "error": "SyntaxError: invalid syntax",
            "content": "def bad(",
        },
    )

    with sqlite3.connect(test_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT error_msg FROM failures WHERE path='bad.py'")
        row = cursor.fetchone()
        assert row is not None
        assert "SyntaxError" in row[0]

        cursor.execute("SELECT reason FROM anti_patterns")
        anti = cursor.fetchone()
        assert anti is not None
        assert "Syntax Error" in anti[0]
