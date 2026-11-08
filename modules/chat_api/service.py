"""
TurnService：对话回合唯一内部入口。

HTTP / ChatAdapter / OpenAI 兼容层都应调用本服务，避免互相 import main。
"""

from __future__ import annotations

import asyncio
import re
import hashlib
import json
from datetime import datetime
from contextlib import contextmanager
import logging
from typing import Any, List
from uuid import uuid4

from fastapi import HTTPException

from agents.router import app as router_graph
from infrastructure.container import (
    get_chat_history,
    get_chat_options,
    get_db_path,
    get_container,
    use_container,
)
from memory.hindsight import get_hindsight_memory, resolve_memory_thread_id

from storage.turn_requests import TurnRequests
from tracing.router_run import run_router_traced

from schemas.turns import TurnRequest, TurnResult
from storage.database import insert_turn

logger = logging.getLogger(__name__)


class TurnService:
    def __init__(self, container=None):
        self.container = container

    @contextmanager
    def scope(self):
        with use_container(self.container or get_container()):
            yield

    def _history(self):
        return self.container.history if self.container else get_chat_history()

    def _memory(self):
        return self.container.memory if self.container else get_hindsight_memory()

    def _store(self):
        return self.container.requests if self.container else TurnRequests(get_db_path())

    def load_history_ui(self, session_id: str, limit: int = 50) -> List[dict]:
        return self._history().get_turns(session_id, limit)

    def run(self, payload: TurnRequest, session_id: str) -> TurnResult:
        with self.scope():
            return self._run(payload, session_id)

    def _run(self, payload: TurnRequest, session_id: str) -> TurnResult:
        conversation_id = session_id
        memory_thread_id = resolve_memory_thread_id(payload.memory_thread_id)

        if payload.workflow_mode == "dev_pipeline":
            raise HTTPException(status_code=410, detail="开发流水线已归档，当前仅运行 Bina 虚拟具身实验。")

        options = get_chat_options()
        if payload.model is not None and payload.model not in options["models"]:
            raise HTTPException(status_code=422, detail="当前模型服务不支持所选模型。")
        if (
            payload.reasoning_effort is not None
            and payload.reasoning_effort not in options["reasoning_levels"]
        ):
            raise HTTPException(status_code=422, detail="当前模型服务不支持所选思考档位。")

        recent_history = self._history().format_for_prompt(conversation_id, limit=5)
        try:
            long_term_context = self._memory().recall(memory_thread_id, payload.text)
        except Exception as exc:
            raise HTTPException(
                status_code=503, detail="Hindsight 记忆召回失败，请检查本机记忆服务。"
            ) from exc
        graph_state: dict[str, Any] = {
            "current_input": payload.text,
            "model": payload.model,
            "reasoning_effort": payload.reasoning_effort,
            # 状态和长期记忆使用稳定用户身份。
            "thread_id": memory_thread_id,
            "conversation_id": conversation_id,
            "recent_history": recent_history,
            "long_term_context": long_term_context,
        }
        result, trace_raw = run_router_traced(router_graph, graph_state)
        reply_raw = str(result.get("final_response", ""))
        intent = result.get("intent")
        if intent is None:
            raise HTTPException(status_code=500, detail="router returned empty intent")
        active_task_type = result.get("active_task_type")
        if active_task_type is None:
            active_task_type = getattr(intent, "task_type", None)
        active_persona = result.get("active_persona") or getattr(intent, "persona", None)

        prefix = "bina"
        reply_clean = re.sub(r"^\s*\[[^\]]+]\s*[:：]\s*", "", str(reply_raw))
        reply_labeled = f"[{prefix}]: {reply_clean}"
        reply_out = reply_clean if payload.strip_persona_prefix else reply_labeled
        return TurnResult(
            reply=reply_out,
            intent=intent,
            trace_raw=list(trace_raw or []),
            active_task_type=str(active_task_type),
            active_persona=str(active_persona or prefix),
        )

    def execute(self, payload: TurnRequest, session_id: str, request_id: str | None = None) -> TurnResult:
        with self.scope():
            return self._execute(payload, session_id, request_id or payload.request_id)

    def _execute(self, payload: TurnRequest, session_id: str, request_id: str | None = None) -> TurnResult:
        """Single entry point: session exclusion covers history, generation and both stores.

        A persisted prepared result allows resuming a failed Hindsight commit without
        regenerating or appending a second local turn. The document ID and timestamp
        stay identical on retries.
        """
        request_id = request_id or uuid4().hex
        store = self._store()
        fingerprint = hashlib.sha256(
            json.dumps(
                {
                    **payload.model_dump(exclude={"request_id"}),
                    "memory_thread_id": resolve_memory_thread_id(payload.memory_thread_id),
                },
                sort_keys=True,
                ensure_ascii=False,
            ).encode()
        ).hexdigest()
        with store.session(session_id):
            record = store.begin(session_id, request_id, fingerprint)
            if record is None:
                try:
                    result = self.run(payload, session_id)
                except BaseException:
                    store.fail(session_id, request_id)
                    raise
                # Initialize the raw-history schema before the atomic local commit.
                self._history()
                saved = result.to_saved()
                labeled = result.reply
                if not re.match(r"^\s*\[[^\]]+]\s*[:：]", labeled):
                    labeled = f"[{result.active_persona}]: {labeled}"
                record = store.prepare(session_id, request_id, saved, payload.text, labeled)
            saved = json.loads(record["result"])
            result = TurnResult.from_saved(saved)
            if record["status"] != "completed":
                try:
                    self._memory().retain_turn(
                        resolve_memory_thread_id(payload.memory_thread_id),
                        session_id,
                        payload.text,
                        re.sub(r"^\s*\[[^\]]+]\s*[:：]\s*", "", result.reply),
                        document_id="bina-request-"
                        + hashlib.sha256(f"{session_id}\0{request_id}".encode()).hexdigest(),
                        timestamp=datetime.fromisoformat(record["recorded_at"]),
                    )
                except Exception as exc:
                    raise HTTPException(
                        503, "对话已保存到本地，长期记忆尚未完成；请使用同一请求 ID 重试。"
                    ) from exc
                store.complete(session_id, request_id)
            return result

    async def aexecute(
        self, payload: TurnRequest, session_id: str, request_id: str | None = None, *, disconnected=None
    ) -> TurnResult:
        """One async coordinator for HTTP, SSE and adapters; SQLite stays off the loop."""
        request_id = request_id or payload.request_id or uuid4().hex
        task = asyncio.create_task(asyncio.to_thread(self.execute, payload, session_id, request_id))
        task.add_done_callback(lambda done: done.exception() if not done.cancelled() else None)
        try:
            if disconnected is None:
                return await asyncio.shield(task)
            while not task.done():
                await asyncio.wait({task}, timeout=0.1)
                if await disconnected():
                    raise HTTPException(499, "客户端已断开。")
            return task.result()
        finally:
            if not task.done():
                try:
                    await asyncio.shield(asyncio.to_thread(self.cancel, session_id, request_id))
                except Exception:
                    logger.exception(
                        "Cancellation persistence failed",
                        extra={"session_id": session_id, "request_id": request_id},
                    )

    def cancel(self, session_id: str, request_id: str):
        return self._store().cancel(session_id, request_id)

    def request_status(self, session_id: str, request_id: str):
        return self._store().get(session_id, request_id)

    def commit_notice(self, session_id: str, generate) -> str:
        """Serialize proactive generation and local commit with user turns.

        Notices are assistant-originated. They do not become user facts in
        Hindsight; only subsequent real user interaction can supply such facts.
        """
        store = self._store()
        with self.scope(), store.session(session_id):
            line = generate()
            if not isinstance(line, str) or not line.strip():
                raise ValueError("Empty proactive notice")
            with store.connect() as connection:
                insert_turn(connection, session_id, "[proactive]", f"[Bina]: {line}", "proactive")
            return line


def get_turn_service() -> TurnService:
    return get_container().turns


__all__ = ["TurnRequest", "TurnResult", "TurnService", "get_turn_service"]
