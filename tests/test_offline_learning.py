import pytest
from fastapi.testclient import TestClient
from project_creator.server import app
import os
import sqlite3
from project_creator.learning import DB_PATH

client = TestClient(app)

def test_get_patterns():
    response = client.get("/learning/patterns")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_delete_pattern():
    # Insert a dummy pattern
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO patterns (pattern_type, content) VALUES ('test', 'test_content')")
        pattern_id = cursor.lastrowid
        conn.commit()

    response = client.delete(f"/learning/patterns/{pattern_id}")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    # Verify deletion
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM patterns WHERE id = ?", (pattern_id,))
        assert cursor.fetchone() is None

def test_trigger_scan():
    # Just test it doesn't crash
    response = client.post("/learning/scan", json={"path": "."})
    assert response.status_code == 200
    assert response.json() == {"status": "scan_complete"}
