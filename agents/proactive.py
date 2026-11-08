"""Per-application proactive interaction, serialized with normal chat turns."""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
from datetime import datetime
import logging
import threading
import time
from uuid import uuid4

from fastapi import HTTPException
from langchain_core.messages import HumanMessage, SystemMessage

from infrastructure.container import use_container
from prompts.system_prompts import BINA_PROMPT_TEMPLATE, with_mood_context

PROACTIVE_USER_MARKER = "[proactive]"
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PresenceTarget:
    session_id: str
    memory_thread_id: str
    updated_at: float = field(default_factory=time.time)


@dataclass
class PendingNotice:
    id: str
    session_id: str
    memory_thread_id: str
    preview: str
    created_at: str
    consumed: bool = False


class ProactiveAgent:
    def __init__(self, container):
        self.container = container
        self._lock = threading.Lock()
        self._presence = None
        self._pending: list[PendingNotice] = []
        self._last_contact: dict[str, float] = {}
        self._task = None
        self._worker = None
        self._stopping = False

    def set_presence(self, session_id: str, memory_thread_id: str | None = None):
        if not session_id.strip():
            raise ValueError("session_id required")
        target = PresenceTarget(
            session_id.strip(), (memory_thread_id or "").strip() or self.container.settings.memory_user_id
        )
        with self._lock:
            self._presence = target
        return target

    def get_presence(self):
        with self._lock:
            return self._presence

    def drain_pending(self):
        with self._lock:
            items = [asdict(notice) for notice in self._pending if not notice.consumed]
            for notice in self._pending:
                notice.consumed = True
            return [{key: value for key, value in item.items() if key != "consumed"} for item in items]

    def in_quiet_hours(self, now=None):
        hour = (now or datetime.now()).hour
        start, end = (
            self.container.settings.proactive_quiet_start,
            self.container.settings.proactive_quiet_end,
        )
        return (start <= hour < end) if start <= end else (hour >= start or hour < end)

    def generate(self, memory_thread_id: str) -> str:
        from prompts.bina_context import build_bina_mode_context
        from prompts.steering import with_style_steering

        mood = self.container.mood
        mode_context, visual_rule = build_bina_mode_context(proactive=True)
        base = BINA_PROMPT_TEMPLATE.format(
            visual_rule=visual_rule, medical_block="", mode_context=mode_context
        )
        prompt = with_style_steering(
            with_mood_context(
                base, mood.get_prompt_context(memory_thread_id), mood.get_style_guidance(memory_thread_id)
            ),
            "bina",
        )
        response = self.container.llm.invoke(
            [
                SystemMessage(content=prompt),
                HumanMessage(
                    content=(
                        "【系统任务·主动开口】陛下一段时间没来找你了。请像私下聊天一样先说一两句短话，"
                        "不超过60字。不列清单、不用客服腔、不以[Bina]:开头。"
                    )
                ),
            ]
        )
        text = response.content
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Proactive model returned no text")
        return text.replace("[Bina]:", "").replace("[bina]:", "").strip()[:120]

    def run_once(self):
        settings = self.container.settings
        target = self.get_presence()
        if self._stopping or not settings.proactive_enabled or self.in_quiet_hours() or target is None:
            return None
        mem, sid = target.memory_thread_id, target.session_id
        with self._lock:
            if time.time() - self._last_contact.get(mem, 0) < settings.proactive_cooldown * 60:
                return None
        with use_container(self.container):
            mood = self.container.mood
            mood.tick_idle(mem)
            if "contact" not in mood.check_triggers(mem):
                return None
            try:

                def generate():
                    line = self.generate(mem)
                    if self._stopping:
                        raise ValueError("Application is stopping")
                    return line

                line = self.container.turns.commit_notice(sid, generate)
            except HTTPException as exc:
                if exc.status_code != 409:
                    logger.exception("Proactive commit failed")
                return None  # Busy user conversation: skip, never interrupt it.
            except Exception:
                logger.exception("Proactive generation or commit failed")
                return None
            mood.apply_delta(mem, connection=-0.35)
            with self._lock:
                self._last_contact[mem] = time.time()
                self._pending.append(
                    PendingNotice(uuid4().hex, sid, mem, line[:80], datetime.now().isoformat())
                )
                self._pending = self._pending[-20:]
            return f"[Bina]: {line}"

    async def _loop(self):
        while not self._stopping:
            self._worker = asyncio.create_task(asyncio.to_thread(self.run_once))
            await asyncio.shield(self._worker)
            self._worker = None
            await asyncio.sleep(self.container.settings.proactive_interval)

    async def start(self):
        if self.container.settings.proactive_enabled and (self._task is None or self._task.done()):
            self._stopping = False
            self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self._stopping = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        # Do not leave an unobserved worker writing after application shutdown.
        if self._worker:
            try:
                await self._worker
            except Exception:
                logger.exception("Proactive shutdown worker failed")
            self._worker = None
