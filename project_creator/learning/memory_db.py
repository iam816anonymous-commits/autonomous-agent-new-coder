import sqlite3
import os
import json

class CodingMemory:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Night Learning stats
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS night_learning_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE DEFAULT CURRENT_DATE,
                    tasks_completed INTEGER DEFAULT 0,
                    patterns_learned INTEGER DEFAULT 0,
                    quota_used INTEGER DEFAULT 0,
                    memory_growth_kb REAL DEFAULT 0
                )
            ''')

            # Anti-patterns learned
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS anti_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT,
                    reason TEXT,
                    severity TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # (Other v13 tables re-included here)
            cursor.execute('CREATE TABLE IF NOT EXISTS patterns (id INTEGER PRIMARY KEY AUTOINCREMENT, pattern_type TEXT, content TEXT, frequency INTEGER DEFAULT 1, preference_score REAL DEFAULT 1.0, last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS snippets (id INTEGER PRIMARY KEY AUTOINCREMENT, file_path TEXT, content TEXT, tags TEXT, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS user_style (key TEXT PRIMARY KEY, value TEXT)')

            conn.commit()

    def log_night_activity(self, tasks, patterns, quota, growth):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO night_learning_stats (tasks_completed, patterns_learned, quota_used, memory_growth_kb)
                VALUES (?, ?, ?, ?)
            ''', (tasks, patterns, quota, growth))
            conn.commit()

    def add_anti_pattern(self, content, reason, severity="LOW"):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO anti_patterns (content, reason, severity) VALUES (?, ?, ?)', (content, reason, severity))
            conn.commit()

    # Restoration of necessary v13 methods
    def learn_pattern(self, p_type, content):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, frequency FROM patterns WHERE pattern_type = ? AND content = ?', (p_type, content))
            row = cursor.fetchone()
            if row: cursor.execute('UPDATE patterns SET frequency = frequency + 1 WHERE id = ?', (row[0],))
            else: cursor.execute('INSERT INTO patterns (pattern_type, content) VALUES (?, ?)', (p_type, content))
            conn.commit()

    def add_snippet(self, path, content, status):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO snippets (file_path, content, status) VALUES (?, ?, ?)', (path, content, status))
            conn.commit()

    def get_top_patterns(self, p_type, limit=10):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT content FROM patterns WHERE pattern_type = ? ORDER BY frequency DESC LIMIT ?', (p_type, limit))
            return [r[0] for r in cursor.fetchall()]
