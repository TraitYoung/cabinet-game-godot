"""Durable turn lifecycle and process-safe per-session exclusion (local SQLite deployment)."""

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

from fastapi import HTTPException
from schemas.turns import RequestRecord
from storage.database import connect, insert_turn, migrate


class TurnRequests:
    def __init__(self, db_path):
        self.db_path = str(db_path)
        migrate(self.db_path)

    def connect(self):
        return connect(self.db_path)

    @contextmanager
    def session(self, session_id):
        directory = Path(self.db_path + ".locks")
        directory.mkdir(exist_ok=True)
        path = directory / hashlib.sha256(session_id.encode()).hexdigest()
        lock = sqlite3.connect(path, timeout=0)
        try:
            try:
                lock.execute("BEGIN IMMEDIATE")
            except sqlite3.OperationalError as exc:
                raise HTTPException(409, "本会话已有回合正在处理，请等待完成后再发送。") from exc
            yield
        finally:
            lock.close()

    def get(self, session_id, request_id):
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM turn_requests WHERE session_id=? AND request_id=?", (session_id, request_id)
            ).fetchone()
        return RequestRecord.model_validate(dict(row)) if row else None

    def begin(self, session_id, request_id, fingerprint):
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM turn_requests WHERE session_id=? AND request_id=?", (session_id, request_id)
            ).fetchone()
            if row:
                if row["fingerprint"] and row["fingerprint"] != fingerprint:
                    raise HTTPException(409, "同一请求 ID 不能用于不同内容或记忆身份。")
                if row["status"] == "cancelled":
                    raise HTTPException(409, "此回合已取消，未提交。")
                if row["status"] in ("committing", "completed"):
                    return RequestRecord.model_validate(dict(row))
            # A crashed generation has no committed data and can be retried under the session lock.
            conn.execute(
                "INSERT INTO turn_requests (session_id, request_id, fingerprint, status, result, recorded_at) VALUES (?, ?, ?, ?, NULL, NULL) ON CONFLICT(session_id,request_id) DO UPDATE SET fingerprint=excluded.fingerprint, status=excluded.status, result=NULL, recorded_at=NULL",
                (session_id, request_id, fingerprint, "generating"),
            )
        return None

    def cancel(self, session_id, request_id):
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "INSERT OR IGNORE INTO turn_requests (session_id, request_id, status) VALUES (?, ?, 'cancelled')",
                (session_id, request_id),
            )
            conn.execute(
                "UPDATE turn_requests SET status='cancelled' WHERE session_id=? AND request_id=? AND status IN ('generating', 'failed')",
                (session_id, request_id),
            )
        return self.get(session_id, request_id)

    def prepare(self, session_id, request_id, result, user_text, labeled):
        # Cancellation and local commit compete in the same SQLite transaction.
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT status FROM turn_requests WHERE session_id=? AND request_id=?",
                (session_id, request_id),
            ).fetchone()
            if row["status"] == "cancelled":
                raise HTTPException(409, "此回合已取消，未提交。")
            if row["status"] != "generating":
                raise ValueError("Only a generating request can enter commit")
            insert_turn(conn, session_id, user_text, labeled)
            conn.execute(
                "UPDATE turn_requests SET status='committing', result=?, recorded_at=? WHERE session_id=? AND request_id=?",
                (
                    json.dumps(result, ensure_ascii=False),
                    datetime.now(timezone.utc).isoformat(),
                    session_id,
                    request_id,
                ),
            )
        return self.get(session_id, request_id)

    def fail(self, session_id, request_id):
        with self.connect() as conn:
            conn.execute(
                "UPDATE turn_requests SET status='failed' WHERE session_id=? AND request_id=? AND status='generating'",
                (session_id, request_id),
            )

    def complete(self, session_id, request_id):
        with self.connect() as conn:
            conn.execute(
                "UPDATE turn_requests SET status='completed' WHERE session_id=? AND request_id=? AND status='committing'",
                (session_id, request_id),
            )
