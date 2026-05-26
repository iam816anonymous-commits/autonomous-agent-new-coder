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

            # Patches and Impact
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
                    latency_before REAL,
                    latency_after REAL,
                    tests_before INTEGER,
                    tests_after INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # User Preferences
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')

            # Version Tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_tag TEXT,
                    accuracy REAL,
                    latency REAL,
                    cost REAL,
                    tests_passed INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Knowledge Graph (Simplified)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_graph (
                    file_path TEXT PRIMARY KEY,
                    dependencies TEXT, -- JSON list
                    owner_agent TEXT,
                    risk_score REAL
                )
            ''')

            conn.commit()

    def get_preferences(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key, value FROM user_preferences')
            return dict(cursor.fetchall())

    def update_preference(self, key, value):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO user_preferences (key, value) VALUES (?, ?)', (key, value))
            conn.commit()

    def update_patch_impact(self, patch_id, impact_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE patch_queue
                SET latency_before = ?, latency_after = ?, tests_before = ?, tests_after = ?
                WHERE id = ?
            ''', (
                impact_data.get('latency_before'),
                impact_data.get('latency_after'),
                impact_data.get('tests_before'),
                impact_data.get('tests_after'),
                patch_id
            ))
            conn.commit()

    def add_version(self, version_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO versions (version_tag, accuracy, latency, cost, tests_passed)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                version_data['tag'],
                version_data.get('accuracy'),
                version_data.get('latency'),
                version_data.get('cost'),
                version_data.get('tests_passed')
            ))
            conn.commit()

    def update_knowledge_graph(self, file_path, deps, owner, risk):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO knowledge_graph (file_path, dependencies, owner_agent, risk_score)
                VALUES (?, ?, ?, ?)
            ''', (file_path, json.dumps(deps), owner, risk))
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
        # Audit log table was missing in updated _init_db, re-adding it for completeness
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, file_path TEXT, audit_type TEXT, result TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('INSERT INTO audit_log (file_path, audit_type, result) VALUES (?, ?, ?)', (file_path, audit_type, result))
            conn.commit()
