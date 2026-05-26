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

            # Evolution History
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS evolution_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    current_version TEXT,
                    candidate_version TEXT,
                    winner TEXT,
                    comparison_data TEXT, -- JSON
                    status TEXT, -- PROMOTED, REJECTED
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Re-initialize all tables from v5
            cursor.execute('CREATE TABLE IF NOT EXISTS knowledge_graph (file_path TEXT PRIMARY KEY, dependencies TEXT, owner_agent TEXT, risk_score REAL, service TEXT, deploy_target TEXT)')
            cursor.execute('CREATE TABLE IF NOT EXISTS environments (name TEXT PRIMARY KEY, current_version TEXT, status TEXT)')
            cursor.execute('CREATE TABLE IF NOT EXISTS deployments (id INTEGER PRIMARY KEY AUTOINCREMENT, env TEXT, version TEXT, patch_id INTEGER, status TEXT, rollback_point TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS telemetry_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, env TEXT, version TEXT, metric TEXT, value REAL, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS patch_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, file_path TEXT, reason TEXT, risk TEXT, affected_tests TEXT, diff TEXT, old_content TEXT, new_content TEXT, status TEXT DEFAULT "PENDING", latency_before REAL, latency_after REAL, tests_before INTEGER, tests_after INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS user_preferences (key TEXT PRIMARY KEY, value TEXT)')
            cursor.execute('CREATE TABLE IF NOT EXISTS versions (id INTEGER PRIMARY KEY AUTOINCREMENT, version_tag TEXT, accuracy REAL, latency REAL, cost REAL, tests_passed INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')

            for env in ['dev', 'staging', 'prod']:
                cursor.execute('INSERT OR IGNORE INTO environments (name, status) VALUES (?, ?)', (env, 'READY'))

            conn.commit()

    def log_evolution(self, current, candidate, winner, comparison):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO evolution_history (current_version, candidate_version, winner, comparison_data)
                VALUES (?, ?, ?, ?)
            ''', (current, candidate, winner, json.dumps(comparison)))
            return cursor.lastrowid

    def update_evolution_status(self, evo_id, status):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE evolution_history SET status = ? WHERE id = ?', (status, evo_id))
            conn.commit()

    # Necessary methods from v5
    def log_deployment(self, env, version, patch_id, status, rollback=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO deployments (env, version, patch_id, status, rollback_point) VALUES (?, ?, ?, ?, ?)', (env, version, patch_id, status, rollback))
            cursor.execute('UPDATE environments SET current_version = ?, status = ? WHERE name = ?', (version, status, env))
            conn.commit()

    def log_telemetry(self, env, version, metric, value):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO telemetry_logs (env, version, metric, value) VALUES (?, ?, ?, ?)', (env, version, metric, value))
            conn.commit()

    def get_latest_telemetry(self, env, metric):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM telemetry_logs WHERE env = ? AND metric = ? ORDER BY timestamp DESC LIMIT 1', (env, metric))
            row = cursor.fetchone()
            return row[0] if row else None

    def get_preferences(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key, value FROM user_preferences')
            return dict(cursor.fetchall())

    def update_knowledge_graph(self, file_path, deps, owner, risk):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO knowledge_graph (file_path, dependencies, owner_agent, risk_score) VALUES (?, ?, ?, ?)', (file_path, json.dumps(deps), owner, risk))
            conn.commit()

    def update_knowledge_graph_env(self, file_path, service, deploy_target):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE knowledge_graph SET service = ?, deploy_target = ? WHERE file_path = ?', (service, deploy_target, file_path))
            conn.commit()

    def add_patch(self, patch_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO patch_queue (file_path, reason, risk, affected_tests, diff, old_content, new_content) VALUES (?, ?, ?, ?, ?, ?, ?)', (patch_data['file'], patch_data['reason'], patch_data['risk'], json.dumps(patch_data['tests']), patch_data['diff'], patch_data['old_content'], patch_data['new_content']))
            return cursor.lastrowid

    def update_patch_status(self, patch_id, status):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE patch_queue SET status = ? WHERE id = ?', (status, patch_id))
            conn.commit()

    def add_version(self, version_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO versions (version_tag, accuracy, latency, cost, tests_passed) VALUES (?, ?, ?, ?, ?)', (version_data['tag'], version_data.get('accuracy', 0), version_data.get('latency', 0), version_data.get('cost', 0), version_data.get('tests_passed', 0)))
            conn.commit()

    def update_preference(self, key, value):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO user_preferences (key, value) VALUES (?, ?)', (key, value))
            conn.commit()

    def log_audit(self, file_path, audit_type, result):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, file_path TEXT, audit_type TEXT, result TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('INSERT INTO audit_log (file_path, audit_type, result) VALUES (?, ?, ?)', (file_path, audit_type, result))
            conn.commit()
