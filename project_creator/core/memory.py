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

            # ROI Metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS roi_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repo_id TEXT,
                    hours_saved REAL,
                    defects_prevented INTEGER,
                    cost_per_run REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Human Trust Metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trust_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patch_id INTEGER,
                    human_acceptance INTEGER,
                    manual_override INTEGER DEFAULT 0,
                    edit_after_accept INTEGER DEFAULT 0,
                    trust_score REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Failure Cemetery
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS failure_cemetery (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id TEXT,
                    reason TEXT,
                    type TEXT,
                    metrics TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Ecosystem Metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ecosystem_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    avg_quality_score REAL,
                    promotion_rate REAL,
                    rollback_rate REAL,
                    drift_rate REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Versions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version_tag TEXT UNIQUE,
                    parent_version TEXT,
                    is_champion INTEGER DEFAULT 0,
                    is_retired INTEGER DEFAULT 0,
                    metrics TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Patch Queue
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patch_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT,
                    reason TEXT,
                    risk TEXT,
                    status TEXT DEFAULT 'PENDING',
                    latency_before REAL,
                    latency_after REAL,
                    tests_before INTEGER,
                    tests_after INTEGER,
                    diff TEXT,
                    old_content TEXT,
                    new_content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Knowledge Graph
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS knowledge_graph (
                    file_path TEXT PRIMARY KEY,
                    dependencies TEXT,
                    owner_agent TEXT,
                    risk_score REAL,
                    service TEXT,
                    deploy_target TEXT
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

            # User Preferences
            cursor.execute('CREATE TABLE IF NOT EXISTS user_preferences (key TEXT PRIMARY KEY, value TEXT)')

            # Evolution Scorecards
            cursor.execute('CREATE TABLE IF NOT EXISTS evolution_scorecards (id INTEGER PRIMARY KEY AUTOINCREMENT, candidate_id TEXT, latency_delta REAL, cost_delta REAL, tests_delta INTEGER, approval_rate REAL, repair_success REAL, promotion_status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')

            conn.commit()

    def add_patch(self, patch_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO patch_queue (file_path, reason, risk, diff, old_content, new_content)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (patch_data['file'], patch_data['reason'], patch_data['risk'],
                  patch_data.get('diff', ''), patch_data.get('old_content', ''), patch_data['new_content']))
            return cursor.lastrowid

    def update_patch_status(self, patch_id, status):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE patch_queue SET status = ? WHERE id = ?', (status, patch_id))
            conn.commit()

    def update_patch_impact(self, patch_id, impact):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE patch_queue SET latency_before = ?, latency_after = ?, tests_before = ?, tests_after = ?
                WHERE id = ?
            ''', (impact.get('latency_before'), impact.get('latency_after'),
                  impact.get('tests_before'), impact.get('tests_after'), patch_id))
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
            conn.commit()

    def log_roi(self, repo, hours, defects, cost):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO roi_metrics (repo_id, hours_saved, defects_prevented, cost_per_run) VALUES (?, ?, ?, ?)', (repo, hours, defects, cost))
            conn.commit()

    def log_trust(self, patch_id, accepted, override, edit, score):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO trust_metrics (patch_id, human_acceptance, manual_override, edit_after_accept, trust_score) VALUES (?, ?, ?, ?, ?)', (patch_id, accepted, override, edit, score))
            conn.commit()

    def add_to_cemetery(self, cid, reason, ftype, metrics):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO failure_cemetery (candidate_id, reason, type, metrics) VALUES (?, ?, ?, ?)', (cid, reason, ftype, json.dumps(metrics)))
            conn.commit()

    def add_version(self, version_data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if version_data.get('is_champion'):
                cursor.execute('UPDATE versions SET is_champion = 0')
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

    def update_knowledge_graph_env(self, file_path, service, target):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE knowledge_graph SET service = ?, deploy_target = ? WHERE file_path = ?', (service, target, file_path))
            conn.commit()

    def add_scorecard(self, scorecard):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO evolution_scorecards (candidate_id, latency_delta, cost_delta, tests_delta, approval_rate, repair_success, promotion_status) VALUES (?, ?, ?, ?, ?, ?, ?)', (scorecard['candidate'], scorecard['latency_delta'], scorecard['cost_delta'], scorecard['tests_delta'], scorecard.get('approval_rate', 0), scorecard.get('repair_success', 0), scorecard['promotion']))
            conn.commit()

    def get_preferences(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key, value FROM user_preferences')
            return dict(cursor.fetchall())

    def log_repo_run(self, data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # This table ecosystem_scorecard was renamed to ecosystem_metrics or similar, but for legacy support:
            cursor.execute('CREATE TABLE IF NOT EXISTS ecosystem_scorecard (id INTEGER PRIMARY KEY AUTOINCREMENT, repo_id TEXT, repair_precision REAL, promotion_rate REAL, rollback_rate REAL, human_override_count INTEGER, constitution_failures INTEGER, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('INSERT INTO ecosystem_scorecard (repo_id, repair_precision, promotion_rate, rollback_rate, human_override_count, constitution_failures) VALUES (?, ?, ?, ?, ?, ?)', (data['repo'], data['repair'], data['promotion'], data['rollback'], data['override'], data['constitution_fail']))
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
