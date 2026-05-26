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

            # Economic Ledger
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS economic_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_id TEXT,
                    hours_saved REAL DEFAULT 0,
                    defects_prevented INTEGER DEFAULT 0,
                    infra_cost REAL DEFAULT 0,
                    review_cost REAL DEFAULT 0,
                    rollback_cost REAL DEFAULT 0,
                    net_value REAL DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Trust Decomposition
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trust_decomposition (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patch_id INTEGER,
                    acceptance INTEGER,
                    override INTEGER,
                    edit_after_accept INTEGER,
                    rollback_after_merge INTEGER,
                    manual_repair INTEGER,
                    trust_score REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Failure Cemetery
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS failure_cemetery (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id TEXT,
                    failure_type TEXT,
                    root_cause TEXT,
                    metrics TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Telemetry
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS telemetry_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    env TEXT,
                    version TEXT,
                    metric TEXT,
                    value REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Deployments
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deployments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    env TEXT,
                    version TEXT,
                    patch_id INTEGER,
                    status TEXT,
                    rollback_point TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Re-initialize other essential tables
            cursor.execute('CREATE TABLE IF NOT EXISTS versions (id INTEGER PRIMARY KEY AUTOINCREMENT, version_tag TEXT UNIQUE, parent_version TEXT, is_champion INTEGER DEFAULT 0, metrics TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS evolution_scorecards (id INTEGER PRIMARY KEY AUTOINCREMENT, candidate_id TEXT, latency_delta REAL, cost_delta REAL, promotion_status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS patch_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, file_path TEXT, reason TEXT, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS ecosystem_metrics (id INTEGER PRIMARY KEY AUTOINCREMENT, avg_quality_score REAL, promotion_rate REAL, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS environments (name TEXT PRIMARY KEY, current_version TEXT, status TEXT)')

            for env in ['dev', 'staging', 'prod']:
                cursor.execute('INSERT OR IGNORE INTO environments (name, status) VALUES (?, ?)', (env, 'READY'))

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

    def log_deployment(self, env, version, patch_id, status, rollback=None):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO deployments (env, version, patch_id, status, rollback_point) VALUES (?, ?, ?, ?, ?)', (env, version, patch_id, status, rollback))
            cursor.execute('UPDATE environments SET current_version = ?, status = ? WHERE name = ?', (version, status, env))
            conn.commit()

    def log_economic_transaction(self, repo, hours, defects, infra, review, rollback=0):
        net_value = hours + defects - infra - review - rollback
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO economic_ledger (repo_id, hours_saved, defects_prevented, infra_cost, review_cost, rollback_cost, net_value)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (repo, hours, defects, infra, review, rollback, net_value))
            conn.commit()

    def log_trust_decomposition(self, patch_id, data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO trust_decomposition (patch_id, acceptance, override, edit_after_accept, rollback_after_merge, manual_repair, trust_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (patch_id, data['acceptance'], data.get('override',0), data.get('edit',0), data.get('rollback',0), data.get('repair',0), data['score']))
            conn.commit()

    def add_to_cemetery(self, cid, ftype, cause, metrics):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO failure_cemetery (candidate_id, failure_type, root_cause, metrics)
                VALUES (?, ?, ?, ?)
            ''', (cid, ftype, cause, json.dumps(metrics)))
            conn.commit()

    def add_version(self, version_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if version_data.get('is_champion'): cursor.execute('UPDATE versions SET is_champion = 0')
            cursor.execute('INSERT OR REPLACE INTO versions (version_tag, parent_version, is_champion, metrics) VALUES (?, ?, ?, ?)', (version_data['tag'], version_data.get('parent'), 1 if version_data.get('is_champion') else 0, json.dumps(version_data.get('metrics', {}))))
            conn.commit()

    def get_champion_version(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT version_tag, metrics FROM versions WHERE is_champion = 1')
            row = cursor.fetchone()
            return (row[0], json.loads(row[1])) if row else (None, {})

    def add_patch(self, patch_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO patch_queue (file_path, reason, status) VALUES (?, ?, ?)', (patch_data['file'], patch_data['reason'], 'PENDING'))
            return cursor.lastrowid

    def update_patch_status(self, patch_id, status):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE patch_queue SET status = ? WHERE id = ?', (status, patch_id))
            conn.commit()

    def update_ecosystem_scoreboard(self, metrics):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO ecosystem_metrics (avg_quality_score, promotion_rate) VALUES (?, ?)', (metrics['quality'], metrics['promotion']))
            conn.commit()

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

    def log_audit(self, file_path, audit_type, result):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, file_path TEXT, audit_type TEXT, result TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('INSERT INTO audit_log (file_path, audit_type, result) VALUES (?, ?, ?)', (file_path, audit_type, result))
            conn.commit()
