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

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS champion_telemetry (
                    version_tag TEXT PRIMARY KEY,
                    repo_id TEXT,
                    candidate_count INTEGER DEFAULT 0,
                    promotions INTEGER DEFAULT 0,
                    retirements INTEGER DEFAULT 0,
                    avg_lifetime_days REAL,
                    net_value REAL DEFAULT 0,
                    benchmark_gain REAL
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trust_decomposition (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patch_id INTEGER,
                    acceptance INTEGER,
                    trust_score REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

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

            cursor.execute('CREATE TABLE IF NOT EXISTS versions (id INTEGER PRIMARY KEY AUTOINCREMENT, version_tag TEXT UNIQUE, parent_version TEXT, is_champion INTEGER DEFAULT 0, metrics TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS patch_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, file_path TEXT, reason TEXT, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS environments (name TEXT PRIMARY KEY, current_version TEXT, status TEXT)')

            for env in ['dev', 'staging', 'prod']:
                cursor.execute('INSERT OR IGNORE INTO environments (name, status) VALUES (?, ?)', (env, 'READY'))

            conn.commit()

    def log_telemetry(self, env, version, metric, value):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO telemetry_logs (env, version, metric, value) VALUES (?, ?, ?, ?)', (env, version, metric, value))
            conn.commit()

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

    def update_champion_telemetry(self, version, repo, data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO champion_telemetry (version_tag, repo_id, promotions, net_value)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(version_tag) DO UPDATE SET
                promotions = promotions + excluded.promotions,
                net_value = net_value + excluded.net_value
            ''', (version, repo, data.get('promotions', 0), data.get('value', 0)))
            conn.commit()

    def add_patch(self, patch_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO patch_queue (file_path, reason, status) VALUES (?, ?, ?)', (patch_data['file'], patch_data['reason'], 'PENDING'))
            return cursor.lastrowid

    def log_trust(self, patch_id, score):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO trust_decomposition (patch_id, acceptance, trust_score) VALUES (?, 1, ?)', (patch_id, score))
            conn.commit()

    def add_version(self, version_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if version_data.get('is_champion'): cursor.execute('UPDATE versions SET is_champion = 0')
            # Manually serialize metrics to JSON string
            metrics_json = json.dumps(version_data.get('metrics', {}))
            cursor.execute('''
                INSERT OR REPLACE INTO versions (version_tag, parent_version, is_champion, metrics)
                VALUES (?, ?, ?, ?)
            ''', (version_data['tag'], version_data.get('parent'), 1 if version_data.get('is_champion') else 0, metrics_json))
            conn.commit()

    def get_champion_version(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT version_tag, metrics FROM versions WHERE is_champion = 1')
            row = cursor.fetchone()
            if row:
                return row[0], json.loads(row[1])
            return None, {}

    def update_patch_status(self, pid, status):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE patch_queue SET status = ? WHERE id = ?', (status, pid))
            conn.commit()

    def get_latest_telemetry(self, env, metric):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM telemetry_logs WHERE env = ? AND metric = ? ORDER BY timestamp DESC LIMIT 1', (env, metric))
            row = cursor.fetchone()
            return row[0] if row else None

    # Stubs or re-implementations for other methods
    def get_preferences(self): return {}
    def update_knowledge_graph(self, *args): pass
    def update_knowledge_graph_env(self, *args): pass
    def log_audit(self, *args): pass
    def add_scorecard(self, *args): pass
    def update_ecosystem_scoreboard(self, *args): pass
    def add_to_cemetery(self, *args): pass
