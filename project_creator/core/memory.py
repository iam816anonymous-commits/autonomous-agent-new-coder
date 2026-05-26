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

            # Operational Ecosystem Scoreboard
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ecosystem_scorecard (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_id TEXT,
                    repair_precision REAL,
                    promotion_rate REAL,
                    rollback_rate REAL,
                    human_override_count INTEGER,
                    constitution_failures INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Champion Telemetry
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS champion_telemetry (
                    version_tag TEXT PRIMARY KEY,
                    candidate_count INTEGER DEFAULT 0,
                    promotions INTEGER DEFAULT 0,
                    retirements INTEGER DEFAULT 0,
                    avg_lifetime_days REAL,
                    benchmark_gain REAL
                )
            ''')

            # Re-initialize all tables from v8
            cursor.execute('CREATE TABLE IF NOT EXISTS ecosystem_metrics (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, avg_quality_score REAL, promotion_rate REAL, rollback_rate REAL, drift_rate REAL)')
            cursor.execute('CREATE TABLE IF NOT EXISTS versions (id INTEGER PRIMARY KEY AUTOINCREMENT, version_tag TEXT UNIQUE, parent_version TEXT, is_champion INTEGER DEFAULT 0, is_retired INTEGER DEFAULT 0, metrics TEXT, deployment_id INTEGER, telemetry_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS evolution_scorecards (id INTEGER PRIMARY KEY AUTOINCREMENT, candidate_id TEXT, latency_delta REAL, cost_delta REAL, tests_delta INTEGER, approval_rate REAL, repair_success REAL, promotion_status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS knowledge_graph (file_path TEXT PRIMARY KEY, dependencies TEXT, owner_agent TEXT, risk_score REAL, service TEXT, deploy_target TEXT)')
            cursor.execute('CREATE TABLE IF NOT EXISTS environments (name TEXT PRIMARY KEY, current_version TEXT, status TEXT)')
            cursor.execute('CREATE TABLE IF NOT EXISTS deployments (id INTEGER PRIMARY KEY AUTOINCREMENT, env TEXT, version TEXT, patch_id INTEGER, status TEXT, rollback_point TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS telemetry_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, env TEXT, version TEXT, metric TEXT, value REAL, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS patch_queue (id INTEGER PRIMARY KEY AUTOINCREMENT, file_path TEXT, reason TEXT, risk TEXT, affected_tests TEXT, diff TEXT, old_content TEXT, new_content TEXT, status TEXT DEFAULT "PENDING", latency_before REAL, latency_after REAL, tests_before INTEGER, tests_after INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS user_preferences (key TEXT PRIMARY KEY, value TEXT)')

            for env in ['dev', 'staging', 'prod']:
                cursor.execute('INSERT OR IGNORE INTO environments (name, status) VALUES (?, ?)', (env, 'READY'))

            conn.commit()

    def log_repo_run(self, data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ecosystem_scorecard (repo_id, repair_precision, promotion_rate, rollback_rate, human_override_count, constitution_failures)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (data['repo'], data['repair'], data['promotion'], data['rollback'], data['override'], data['constitution_fail']))
            conn.commit()

    def update_champion_telemetry(self, version, data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO champion_telemetry (version_tag, candidate_count, promotions, benchmark_gain)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(version_tag) DO UPDATE SET
                candidate_count = candidate_count + excluded.candidate_count,
                promotions = promotions + excluded.promotions,
                benchmark_gain = excluded.benchmark_gain
            ''', (version, data.get('candidates', 0), data.get('promotions', 0), data.get('gain', 0)))
            conn.commit()

    # Core lineage and version methods
    def add_version(self, version_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if version_data.get('is_champion'):
                cursor.execute('UPDATE versions SET is_champion = 0 WHERE is_champion = 1')
            cursor.execute('INSERT OR REPLACE INTO versions (version_tag, parent_version, is_champion, metrics) VALUES (?, ?, ?, ?)', (version_data['tag'], version_data.get('parent'), 1 if version_data.get('is_champion') else 0, json.dumps(version_data.get('metrics', {}))))
            conn.commit()

    def get_champion_version(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT version_tag, metrics FROM versions WHERE is_champion = 1')
            row = cursor.fetchone()
            return (row[0], json.loads(row[1])) if row else (None, {})

    def retire_champion(self, version_tag):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE versions SET is_champion = 0, is_retired = 1 WHERE version_tag = ?', (version_tag,))
            cursor.execute('UPDATE champion_telemetry SET retirements = retirements + 1 WHERE version_tag = ?', (version_tag,))
            conn.commit()

    # Operational Support
    def add_scorecard(self, scorecard_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO evolution_scorecards (candidate_id, latency_delta, cost_delta, tests_delta, approval_rate, repair_success, promotion_status) VALUES (?, ?, ?, ?, ?, ?, ?)', (scorecard_data['candidate'], scorecard_data['latency_delta'], scorecard_data['cost_delta'], scorecard_data['tests_delta'], scorecard_data['approval_rate'], scorecard_data['repair_success'], scorecard_data['promotion']))
            conn.commit()

    def update_ecosystem_scoreboard(self, metrics):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO ecosystem_metrics (avg_quality_score, promotion_rate, rollback_rate, drift_rate) VALUES (?, ?, ?, ?)', (metrics['quality'], metrics['promotion'], metrics['rollback'], metrics['drift']))
            conn.commit()

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

    def get_preferences(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key, value FROM user_preferences')
            return dict(cursor.fetchall())

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

    def log_audit(self, file_path, audit_type, result):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, file_path TEXT, audit_type TEXT, result TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('INSERT INTO audit_log (file_path, audit_type, result) VALUES (?, ?, ?)', (file_path, audit_type, result))
            conn.commit()

    def update_preference(self, key, value):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO user_preferences (key, value) VALUES (?, ?)', (key, value))
            conn.commit()
