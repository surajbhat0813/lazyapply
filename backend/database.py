import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "../data/tracker.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                company     TEXT NOT NULL,
                location    TEXT,
                url         TEXT,
                platform    TEXT,
                score       INTEGER,
                recommendation TEXT,
                description TEXT,
                status      TEXT NOT NULL DEFAULT 'saved',
                notes       TEXT DEFAULT '',
                saved_at    TEXT NOT NULL DEFAULT (datetime('now')),
                applied_at  TEXT
            )
        """)
        conn.commit()
