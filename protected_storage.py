"""Prepared storage protection. Keep this file unchanged for the project.

One process, one Store, a file database, and a separate connection per call.
The re-entrant lock serialises this Store's writers. BEGIN IMMEDIATE also takes
SQLite's writer reservation before a request reads the state it will change.
A failed body or commit rolls back the whole transaction, then closes the
connection. No retry policy is needed for this project.
"""
import sqlite3
import threading
from contextlib import contextmanager


class ProtectedStorage:
    def __init__(self, database):
        self.database = str(database)
        self._write_lock = threading.RLock()
        connection = self.connect()
        try:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS links (
                    code TEXT PRIMARY KEY,
                    destination TEXT NOT NULL,
                    clicks INTEGER NOT NULL DEFAULT 0 CHECK(clicks >= 0)
                );
                CREATE TABLE IF NOT EXISTS buckets (
                    client TEXT NOT NULL,
                    window_start INTEGER NOT NULL,
                    accepted INTEGER NOT NULL CHECK(accepted >= 0),
                    PRIMARY KEY (client, window_start)
                );
            """)
        finally:
            connection.close()

    def connect(self):
        """Open for the current calling thread. The caller must close it."""
        return sqlite3.connect(self.database, timeout=10, isolation_level=None)

    @contextmanager
    def read(self):
        connection = self.connect()
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def write(self):
        with self._write_lock:
            connection = self.connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                yield connection
                connection.commit()
            except BaseException:
                if connection.in_transaction:
                    connection.rollback()
                raise
            finally:
                connection.close()

    def accept_redirect(self, client, code, now):
        """Approved complete operation. Do not duplicate its row changes.

        The context manager commits before this method returns. A failed commit
        raises instead of returning a successful redirect. Both row writes are
        inside the same transaction and the write lock covers the reads too.
        """
        window = int(now // 60) * 60
        with self.write() as connection:
            link = connection.execute(
                "SELECT destination FROM links WHERE code = ?", (code,)).fetchone()
            if link is None:
                return 404, None
            bucket = connection.execute(
                "SELECT accepted FROM buckets WHERE client = ? AND window_start = ?",
                (client, window)).fetchone()
            used = 0 if bucket is None else bucket[0]
            if used >= 5:
                return 429, None
            connection.execute(
                "UPDATE links SET clicks = clicks + 1 WHERE code = ?", (code,))
            if bucket is None:
                connection.execute(
                    "INSERT INTO buckets (client, window_start, accepted) VALUES (?, ?, 1)",
                    (client, window))
            else:
                connection.execute(
                    "UPDATE buckets SET accepted = accepted + 1 "
                    "WHERE client = ? AND window_start = ?", (client, window))
            return 302, link[0]
