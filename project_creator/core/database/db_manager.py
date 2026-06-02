import sqlite3
import os
import time
from contextlib import contextmanager

class DatabaseManager:
    """
    Centralized thread-safe connection and transaction management for SQLite.
    """
    def __init__(self, db_path):
        self.db_path = db_path

    @contextmanager
    def connection(self):
        """Yields a database connection with automatic closing."""
        conn = sqlite3.connect(self.db_path, timeout=10)
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self):
        """Yields a cursor within a transaction context."""
        with self.connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e

    def execute_query(self, query, params=()):
        """Executes a single query and returns results."""
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_commit(self, query, params=()):
        """Executes a commit query."""
        with self.transaction() as cursor:
            cursor.execute(query, params)
            return cursor.lastrowid
