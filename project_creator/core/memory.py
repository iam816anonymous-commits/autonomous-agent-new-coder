import sqlite3
import os
import json

class MemoryLayer:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Patches table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patch_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT,
                    reason TEXT,
                    risk TEXT,
                    affected_tests TEXT,
                    diff TEXT,
                    old_content TEXT,
                    new_content TEXT,
                    status TEXT DEFAULT 'PENDING',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Audit log
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT,
                    audit_type TEXT,
                    result TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Benchmarks
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS benchmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patch_id INTEGER,
                    metric TEXT,
                    value REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # User preferences (Memory)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT,
                    count INTEGER DEFAULT 1,
                    outcome TEXT -- 'ACCEPTED' or 'REJECTED'
                )
            ''')
            conn.commit()

    def add_patch(self, patch_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO patch_queue (file_path, reason, risk, affected_tests, diff, old_content, new_content)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                patch_data['file'],
                patch_data['reason'],
                patch_data['risk'],
                json.dumps(patch_data['tests']),
                patch_data['diff'],
                patch_data['old_content'],
                patch_data['new_content']
            ))
            return cursor.lastrowid

    def update_patch_status(self, patch_id, status):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE patch_queue SET status = ? WHERE id = ?', (status, patch_id))
            conn.commit()

    def log_audit(self, file_path, audit_type, result):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO audit_log (file_path, audit_type, result) VALUES (?, ?, ?)', (file_path, audit_type, result))
            conn.commit()

    def record_benchmark(self, patch_id, metric, value):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO benchmarks (patch_id, metric, value) VALUES (?, ?, ?)', (patch_id, metric, value))
            conn.commit()

    def update_preference(self, pattern, outcome):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, count FROM preferences WHERE pattern = ? AND outcome = ?', (pattern, outcome))
            row = cursor.fetchone()
            if row:
                cursor.execute('UPDATE preferences SET count = count + 1 WHERE id = ?', (row[0],))
            else:
                cursor.execute('INSERT INTO preferences (pattern, outcome) VALUES (?, ?)', (pattern, outcome))
            conn.commit()
