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

            # Learning Tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT, -- 'import', 'naming', 'api'
                    content TEXT,
                    frequency INTEGER DEFAULT 1,
                    preference_score REAL DEFAULT 1.0,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS snippets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT,
                    content TEXT,
                    tags TEXT, -- JSON list
                    status TEXT, -- APPROVED, MERGED
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_style (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')

            cursor.execute('CREATE TABLE IF NOT EXISTS frameworks (name TEXT PRIMARY KEY, use_count INTEGER DEFAULT 1)')

            conn.commit()

    def learn_pattern(self, p_type, content):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, frequency FROM patterns WHERE pattern_type = ? AND content = ?', (p_type, content))
            row = cursor.fetchone()
            if row:
                cursor.execute('UPDATE patterns SET frequency = frequency + 1, last_seen = CURRENT_TIMESTAMP WHERE id = ?', (row[0],))
            else:
                cursor.execute('INSERT INTO patterns (pattern_type, content) VALUES (?, ?)', (p_type, content))
            conn.commit()

    def add_snippet(self, path, content, status):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO snippets (file_path, content, status) VALUES (?, ?, ?)', (path, content, status))
            conn.commit()

    def update_style(self, key, value):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO user_style (key, value) VALUES (?, ?)', (key, value))
            conn.commit()

    def get_top_patterns(self, p_type, limit=10):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT content FROM patterns WHERE pattern_type = ? ORDER BY frequency DESC LIMIT ?', (p_type, limit))
            return [r[0] for r in cursor.fetchall()]
