"""Interaction failures must stay responsive and must not become memories."""

import asyncio
from io import BytesIO
import threading
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

from fastapi import UploadFile
from fastapi.testclient import TestClient

import agents.router as router
import modules.chat_api.routes as main
from app.factory import create_app
from config.settings import Settings
from infrastructure.container import Container
import modules.chat_api.service as service


class UploadResponsivenessTests(unittest.IsolatedAsyncioTestCase):
    async def check_responsive(self, handler, parameter, target, result):
        entered = threading.Event()
        release = threading.Event()

        def blocking_service(*args, **kwargs):
            entered.set()
            if not release.wait(2):
                raise TimeoutError("The event loop did not release the worker")
            return result

        upload = UploadFile(filename="sample.webm", file=BytesIO(b"sample"))
        with patch(target, side_effect=blocking_service):
            task = asyncio.create_task(handler(**{parameter: upload}))
            try:
                async with asyncio.timeout(1):
                    while not entered.is_set():
                        await asyncio.sleep(0.01)
                # Another request/timer can run while the service is still blocked.
                self.assertFalse(task.done())
            finally:
                release.set()
                await task
                await upload.close()

    async def test_attachment_processing_leaves_event_loop_responsive(self):
        await self.check_responsive(
            main.attachments_ingest_api, "file",
            "modules.attachments.service.ingest_bytes",
            SimpleNamespace(name="sample.txt", kind="text", text="hello", truncated=False),
        )

    async def test_transcription_leaves_event_loop_responsive(self):
        await self.check_responsive(
            main.stt_api, "audio", "modules.stt.service.transcribe_audio", "hello",
        )


class ModelFailureTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.db_path = str(Path(directory.name) / "chat.db")

    def test_failed_or_empty_model_reply_is_not_persisted(self):
        for content in (RuntimeError("private provider diagnostic"), "", "   "):
            for endpoint in ("/api/v1/chat", "/api/v1/chat/stream", "/v1/chat/completions"):
                with self.subTest(content=repr(content), endpoint=endpoint):
                    llm = MagicMock()
                    if isinstance(content, Exception):
                        llm.invoke.side_effect = content
                    else:
                        llm.invoke.return_value.content = content
                    memory = MagicMock()
                    memory.recall.return_value = ""
                    history = MagicMock()
                    history.format_for_prompt.return_value = []
                    with patch.object(router, "get_turn_llm", return_value=llm), \
                            patch.object(router, "get_mood_engine"), \
                            patch.object(router, "search_enabled", return_value=False), \
                            patch.object(service, "get_hindsight_memory", return_value=memory), \
                            patch.object(service, "get_chat_history", return_value=history):
                        payload = {"text": "你好"} if endpoint.startswith("/api/") else {
                            "messages": [{"role": "user", "content": "你好"}],
                        }
                        dependencies = Container(Settings(db_path=self.db_path, proactive_enabled=False))
                        dependencies.history = history
                        dependencies.memory = memory
                        response = TestClient(create_app(container=dependencies)).post(endpoint, json=payload)
                    if endpoint.endswith("/stream"):
                        self.assertIn('"type": "error"', response.text)
                        self.assertNotIn('"type": "done"', response.text)
                    else:
                        self.assertEqual(response.status_code, 502)
                    self.assertNotIn("private provider diagnostic", response.text)
                    history.append_turn.assert_not_called()
                    memory.retain_turn.assert_not_called()


if __name__ == "__main__":
    unittest.main()
