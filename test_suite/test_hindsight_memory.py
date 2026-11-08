"""离线检查 Hindsight 接入边界，不调用外部模型。"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from storage.chat_history import ChatHistory
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

import main
from app.factory import create_app
from config.settings import Settings
from infrastructure.container import Container, use_container
import agents.router as router
import modules.chat_api.service as service
from memory.hindsight import HindsightMemory, resolve_memory_thread_id
from agents.solo_fast import synthesize_solo_bina_intent


class HindsightAdapterTests(unittest.TestCase):
    def test_stable_identity_and_distinct_user_banks(self):
        with use_container(Container(Settings(memory_user_id="local-test"))):
            self.assertEqual(resolve_memory_thread_id(None), "local-test")
            self.assertEqual(resolve_memory_thread_id("  user-a  "), "user-a")
            memory = HindsightMemory()
            self.assertEqual(memory.bank_id(), memory.bank_id("local-test"))
            self.assertNotEqual(memory.bank_id("user-a"), memory.bank_id("user-b"))

    def test_recall_keeps_time_source_and_memory_rules(self):
        memory = HindsightMemory()
        client = MagicMock()
        client.reflect.return_value = SimpleNamespace(
            text="[记录时间=2026-11-05; 来源=turn-2] 用户已搬到杭州，之前住苏州。"
        )
        with patch.object(memory, "_client") as factory:
            factory.return_value.__enter__.return_value = client
            block = memory.recall("same-user", "我现在住在哪里？")
        self.assertIn("明确更正优先", block)
        self.assertIn("2026-11-05", block)
        self.assertIn("turn-2", block)
        self.assertIn("杭州", block)
        self.assertEqual(client.reflect.call_args.kwargs["fact_types"], ["world", "experience"])

    def test_retain_is_synchronous_and_preserves_speakers(self):
        memory = HindsightMemory()
        client = MagicMock()
        with patch.object(memory, "_client") as factory:
            factory.return_value.__enter__.return_value = client
            memory.retain_turn("same-user", "conversation-2", "我已搬家", "记住了", document_id="turn-2")
        args = client.retain.call_args.kwargs
        self.assertFalse(args["retain_async"])
        self.assertEqual(args["update_mode"], "replace")
        self.assertEqual(args["document_id"], "turn-2")
        self.assertEqual(args["metadata"]["conversation_id"], "conversation-2")
        self.assertIn("用户 (", args["content"])
        self.assertIn("Bina (", args["content"])

    def test_bina_prompt_includes_recalled_experience(self):
        llm = MagicMock()
        llm.invoke.return_value.content = "星河杯"
        state = {"thread_id": "user", "intent": synthesize_solo_bina_intent("还记得杯子吗"),
                 "recent_history": [], "long_term_context": "共同经历：我们给蓝色马克杯起名星河杯"}
        with patch.object(router, "get_turn_llm", return_value=llm), \
                patch.object(router, "get_mood_engine"), \
                patch.object(router, "search_enabled", return_value=False):
            result = router.node_bina(state)
        self.assertIn("共同经历", llm.invoke.call_args.args[0][-1].content)
        self.assertEqual(result["active_persona"], "bina")


class ChatEntryPointTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        db_path = str(Path(directory.name) / "chat.db")
        raw_history = ChatHistory(db_path)
        self.memory = MagicMock()
        self.memory.recall.return_value = "【Hindsight 长期记忆】用户住杭州。"
        self.states = []
        self.events = []

        def graph(_graph, state):
            self.states.append(state)
            self.events.append("reply")
            return {"final_response": "杭州", "intent": synthesize_solo_bina_intent(state["current_input"]),
                    "active_task_type": "emotion", "active_persona": "bina"}, []

        self.memory.retain_turn.side_effect = lambda *a, **kw: self.events.append("retain")
        self.history = MagicMock(wraps=raw_history)
        self.history.format_for_prompt.return_value = []
        patches = [
            patch.object(service, "get_db_path", return_value=db_path),
            patch.object(service, "get_hindsight_memory", return_value=self.memory),
            patch.object(service, "get_chat_history", return_value=self.history),
            patch.object(service, "run_router_traced", side_effect=graph),
            patch.dict(os.environ, {"AX_MEMORY_USER_ID": "local-test"}),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        dependencies = Container(Settings(db_path=db_path, memory_user_id="local-test", proactive_enabled=False))
        dependencies.history = self.history
        dependencies.memory = self.memory
        self.client = TestClient(create_app(container=dependencies))

    def test_new_conversations_share_memory_and_wait_for_retain(self):
        for conversation in ("conversation-a", "conversation-b"):
            response = self.client.post("/api/v1/chat", json={"text": "我住哪里？"}, headers={"x-session-id": conversation})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(self.events[-1], "retain")
        self.assertEqual([s["thread_id"] for s in self.states], ["local-test", "local-test"])
        self.assertNotEqual(self.history.format_for_prompt.call_args_list[0].args[0], self.history.format_for_prompt.call_args_list[1].args[0])
        self.assertIn("杭州", self.states[1]["long_term_context"])
        self.assertEqual(self.memory.retain_turn.call_count, 2)

    def test_explicit_memory_pool_is_used_by_both_recall_and_retain(self):
        response = self.client.post("/api/v1/chat", json={"text": "你好"}, headers={"x-memory-thread": "browser-user"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.memory.recall.call_args.args[0], "browser-user")
        self.assertEqual(self.memory.retain_turn.call_args.args[0], "browser-user")

    def test_stream_done_follows_memory_commit(self):
        response = self.client.post("/api/v1/chat/stream", json={"text": "你好"})
        self.assertIn('"type": "done"', response.text)
        self.assertEqual(self.events, ["reply", "retain"])
        self.assertEqual(self.memory.retain_turn.call_count, 1)

    def test_openai_entry_uses_the_same_memory_pipeline(self):
        response = self.client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "你好"}]},
                                    headers={"x-memory-thread": "browser-user"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.memory.retain_turn.call_count, 1)
        self.assertEqual(self.memory.recall.call_args.args[0], "browser-user")

    def test_request_retry_uses_one_local_turn_and_one_memory_document(self):
        payload = {"text": "你好", "request_id": "same-request"}
        headers = {"x-session-id": "idempotent"}
        first = self.client.post("/api/v1/chat", json=payload, headers=headers)
        second = self.client.post("/api/v1/chat", json=payload, headers=headers)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["reply"], second.json()["reply"])
        self.assertEqual(first.headers["x-request-id"], "same-request")
        self.assertEqual(len(self.history.get_turns("idempotent")), 1)
        self.memory.retain_turn.assert_called_once()
        status = self.client.get("/api/v1/chat/requests/same-request", headers=headers).json()
        self.assertEqual(status["status"], "completed")
        cancel = self.client.post("/api/v1/chat/requests/same-request/cancel", headers=headers).json()
        self.assertEqual(cancel["status"], "completed")

    def test_recall_failure_is_visible(self):
        self.memory.recall.side_effect = ConnectionError("offline")
        response = self.client.post("/api/v1/chat", json={"text": "你好"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.states, [])

    def test_write_failure_does_not_report_success(self):
        self.memory.retain_turn.side_effect = ConnectionError("offline")
        response = self.client.post("/api/v1/chat", json={"text": "记住我"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("长期记忆", response.json()["detail"])

    def test_stream_failure_emits_error_without_done(self):
        self.memory.retain_turn.side_effect = ConnectionError("offline")
        response = self.client.post("/api/v1/chat/stream", json={"text": "记住我"})
        self.assertIn('"type": "error"', response.text)
        self.assertNotIn('"type": "done"', response.text)


if __name__ == "__main__":
    unittest.main()
