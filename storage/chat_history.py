"""只保存原始聊天记录，沿用已有 chat_turns 表。"""

from storage.database import connect, insert_turn, migrate


class ChatHistory:
    def __init__(self, db_path: str):
        self.db_path = db_path
        migrate(db_path)

    def _connect(self):
        return connect(self.db_path)

    def append_turn(self, session_id: str, user_text: str, assistant_text: str) -> int:
        with self._connect() as connection:
            return insert_turn(connection, session_id, user_text, assistant_text)

    def get_turns(self, session_id: str, limit: int = 50) -> list[dict[str, str]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT user_text, assistant_text, created_at FROM chat_turns WHERE thread_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, max(1, limit)),
            ).fetchall()
        return [
            {"user": user, "assistant": assistant, "ts": str(timestamp or "")}
            for user, assistant, timestamp in reversed(rows)
        ]

    def format_for_prompt(self, session_id: str, limit: int = 5) -> list[str]:
        # Budget each side before adding labels; message text may itself contain labels.
        return [
            f"User: {turn['user'][:350]}\nBina: {turn['assistant'][:400]}"
            for turn in self.get_turns(session_id, limit)
        ]
