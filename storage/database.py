"""SQLite connections and idempotent, versioned migrations for local state."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3


@contextmanager
def connect(db_path: str, timeout: float = 10):
    connection = sqlite3.connect(db_path, timeout=timeout)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def migrate(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY)")
        conn.execute("""CREATE TABLE IF NOT EXISTS chat_turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT, thread_id TEXT NOT NULL,
            user_text TEXT NOT NULL, assistant_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_turns_thread_created ON chat_turns (thread_id, created_at)"
        )
        conn.execute("""CREATE TABLE IF NOT EXISTS mood_state (
            thread_id TEXT PRIMARY KEY, connection REAL NOT NULL DEFAULT 0,
            pride REAL NOT NULL DEFAULT 0, valence REAL NOT NULL DEFAULT 0,
            arousal REAL NOT NULL DEFAULT 0, immersion REAL NOT NULL DEFAULT 0.3,
            last_tick_at TIMESTAMP, last_interaction_at TIMESTAMP)""")
        mood_columns = {row[1] for row in conn.execute("PRAGMA table_info(mood_state)")}
        if "last_interaction_at" not in mood_columns:
            conn.execute("ALTER TABLE mood_state ADD COLUMN last_interaction_at TIMESTAMP")
            conn.execute("UPDATE mood_state SET last_interaction_at=last_tick_at")
        conn.execute("""CREATE TABLE IF NOT EXISTS turn_requests (
            session_id TEXT NOT NULL, request_id TEXT NOT NULL, fingerprint TEXT,
            status TEXT NOT NULL, result TEXT, recorded_at TEXT,
            PRIMARY KEY(session_id, request_id))""")
        chat_columns = {row[1] for row in conn.execute("PRAGMA table_info(chat_turns)")}
        if "source" not in chat_columns:
            conn.execute("ALTER TABLE chat_turns ADD COLUMN source TEXT NOT NULL DEFAULT 'user'")
            conn.execute("UPDATE chat_turns SET source='proactive' WHERE user_text='[proactive]'")
        conn.execute("INSERT OR IGNORE INTO schema_migrations(version) VALUES (1)")


def insert_turn(conn, session_id: str, user_text: str, assistant_text: str, source: str = "user") -> int:
    cursor = conn.execute(
        "INSERT INTO chat_turns (thread_id, user_text, assistant_text, source) VALUES (?, ?, ?, ?)",
        (session_id, user_text, assistant_text, source),
    )
    return int(cursor.lastrowid)
