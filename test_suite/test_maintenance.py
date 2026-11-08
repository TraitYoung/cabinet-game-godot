"""Maintainability contracts: isolated apps, migrations, cancellation and ownership."""

import asyncio
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.factory import create_app
from config.settings import Settings
from infrastructure.container import Container
from infrastructure.processes import members
from schemas.turns import TurnRequest, TurnResult
from agents.solo_fast import synthesize_solo_bina_intent
from storage.database import migrate
from storage.turn_requests import TurnRequests


class SettingsTests(unittest.TestCase):
    def test_booleans_numbers_aliases_and_secret_safe_validation(self):
        for value in ("0", "false", "OFF", "no"):
            self.assertFalse(Settings.load({"AX_PROACTIVE_ENABLED": value}, env_file=None).proactive_enabled)
        for value in ("1", "true", "ON", "yes"):
            self.assertTrue(Settings.load({"AX_PROACTIVE_ENABLED": value}, env_file=None).proactive_enabled)
        settings = Settings.load(
            {
                "LLM_MODEL": "old-alias",
                "LLM_API_KEY": "secret",
                "DEEPSEEK_BASE_URL": "https://example.com/v1/",
            },
            env_file=None,
        )
        self.assertEqual(settings.chat_model, "old-alias")
        self.assertEqual(settings.deepseek_base_url, "https://example.com")
        self.assertNotIn("secret", repr(settings))
        with self.assertRaises(ValidationError) as caught:
            Settings.load(
                {"AX_REUNION_GAP_MINUTES": "bad-number", "DEEPSEEK_API_KEY": "private-token"}, env_file=None
            )
        self.assertIn("AX_REUNION_GAP_MINUTES", str(caught.exception))
        self.assertNotIn("private-token", str(caught.exception))

    def test_import_does_not_validate_or_connect_to_real_configuration(self):
        import os

        result = subprocess.run(
            [sys.executable, "-c", "import main; assert main.app.state.container._settings is None"],
            env={**os.environ, "AX_REUNION_GAP_MINUTES": "not-a-number"},
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode())


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def dependencies(self, name):
        deps = Container(
            Settings(
                db_path=str(self.root / f"{name}.db"),
                memory_user_id=name,
                proactive_enabled=False,
                image_enabled=False,
                search_enabled=False,
            )
        )
        deps.memory = MagicMock()
        deps.memory.recall.return_value = ""
        deps.llm = MagicMock()
        deps.llm.invoke.return_value.content = "reply for " + name
        return deps

    def test_two_apps_have_separate_history_mood_presence_and_models(self):
        first, second = self.dependencies("first"), self.dependencies("second")
        app1, app2 = create_app(container=first), create_app(container=second)
        self.assertIsNot(app1, app2)
        for app, deps in ((app1, first), (app2, second)):
            with TestClient(app) as client:
                response = client.post(
                    "/api/v1/chat",
                    json={"text": "hello", "request_id": "same-id"},
                    headers={"x-session-id": "same-session"},
                )
                self.assertEqual(response.status_code, 200, response.text)
                self.assertIn(deps.settings.memory_user_id, response.json()["reply"])
                client.post("/api/v1/presence", json={"session_id": deps.settings.memory_user_id})
            self.assertEqual(len(deps.history.get_turns("same-session")), 1)
        first.mood.apply_delta("same-user", valence=0.4)
        self.assertEqual(second.mood.get_state("same-user").valence, 0)
        self.assertNotEqual(first.proactive.get_presence(), second.proactive.get_presence())
        self.assertIsNot(first.llm, second.llm)

    def test_compatibility_fields_and_openapi_only_describe_current_bina(self):
        deps = self.dependencies("compat")
        client = TestClient(create_app(container=deps))
        archived = client.post("/api/v1/chat", json={"text": "hello", "workflow_mode": "dev_pipeline"})
        self.assertEqual(archived.status_code, 410)
        reply = client.post(
            "/api/v1/chat", json={"text": "hello", "forced_persona": "jean", "group_mode": True}
        )
        self.assertEqual(reply.json()["active_persona"], "bina")
        schema = json.dumps(client.get("/openapi.json").json(), ensure_ascii=False)
        for outdated in ("内阁路由", "11 人", "强制本轮说话人设"):
            self.assertNotIn(outdated, schema)

    def test_notice_uses_session_lock_and_never_retains_fake_user_facts(self):
        deps = self.dependencies("notice")
        store = TurnRequests(deps.settings.db_path)
        generate = MagicMock(return_value="Hello from Bina")
        with store.session("session"), self.assertRaises(HTTPException):
            deps.turns.commit_notice("session", generate)
        generate.assert_not_called()
        deps.turns.commit_notice("session", generate)
        self.assertEqual(deps.history.get_turns("session")[0]["user"], "[proactive]")
        with closing(sqlite3.connect(deps.settings.db_path)) as conn:
            self.assertEqual(conn.execute("SELECT source FROM chat_turns").fetchone()[0], "proactive")
        deps.memory.retain_turn.assert_not_called()
        with (
            patch.object(deps.turns, "commit_notice", side_effect=OSError("disk")),
            self.assertLogs("agents.proactive", level="ERROR"),
        ):
            agent = deps.proactive
            agent.set_presence("session")
            with (
                patch.object(agent, "in_quiet_hours", return_value=False),
                patch.object(deps.mood, "check_triggers", return_value=["contact"]),
            ):
                # Enable just this isolated runtime; no application loop is started.
                deps._settings = deps.settings.model_copy(update={"proactive_enabled": True})
                self.assertIsNone(agent.run_once())
                self.assertEqual(agent.drain_pending(), [])

    def test_proactive_notification_follows_successful_shared_commit(self):
        deps = self.dependencies("notice-success")
        deps._settings = deps.settings.model_copy(update={"proactive_enabled": True, "proactive_cooldown": 0})
        agent = deps.proactive
        agent.set_presence("session")
        with (
            patch.object(agent, "in_quiet_hours", return_value=False),
            patch.object(deps.mood, "check_triggers", return_value=["contact"]),
            patch.object(agent, "generate", return_value="A short notice") as generate,
        ):
            with TurnRequests(deps.settings.db_path).session("session"):
                self.assertIsNone(agent.run_once())
                generate.assert_not_called()
                self.assertEqual(agent.drain_pending(), [])
            self.assertEqual(agent.run_once(), "[Bina]: A short notice")
            self.assertEqual(len(agent.drain_pending()), 1)
            self.assertEqual(agent.drain_pending(), [])
            self.assertEqual(len(deps.history.get_turns("session")), 1)
            deps.memory.retain_turn.assert_not_called()

    def test_additive_migration_saved_versions_and_atomic_rollback(self):
        path = str(self.root / "old.db")
        with closing(sqlite3.connect(path)) as conn, conn:
            conn.execute(
                "CREATE TABLE chat_turns(id INTEGER PRIMARY KEY, thread_id TEXT, user_text TEXT, assistant_text TEXT, created_at TEXT)"
            )
            conn.execute("INSERT INTO chat_turns VALUES(1,'s','[proactive]','old notice','old')")
        migrate(path)
        migrate(path)
        with closing(sqlite3.connect(path)) as conn, conn:
            conn.execute("ALTER TABLE turn_requests ADD COLUMN diagnostic TEXT")
            self.assertEqual(conn.execute("SELECT source FROM chat_turns").fetchone()[0], "proactive")
        store = TurnRequests(path)
        store.begin("s", "one", "hash")
        result = TurnResult(
            reply="hello",
            intent=synthesize_solo_bina_intent("hello"),
            active_task_type="emotion",
            active_persona="bina",
        )
        unversioned = result.model_dump()
        self.assertEqual(TurnResult.from_saved(unversioned), result)
        self.assertEqual(TurnResult.from_saved(result.to_saved()), result)
        with self.assertRaises(ValueError):
            TurnResult.from_saved({**unversioned, "version": 99})
        with (
            patch("storage.turn_requests.json.dumps", side_effect=ValueError("serialize")),
            self.assertRaises(ValueError),
        ):
            store.prepare("s", "one", result.to_saved(), "user", "hello")
        self.assertEqual(store.get("s", "one").status, "generating")
        with closing(sqlite3.connect(path)) as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM chat_turns").fetchone()[0], 1)

    def test_cancellation_database_wait_does_not_block_loop_or_replace_original_error(self):
        deps = self.dependencies("cancel")
        entered, release = threading.Event(), threading.Event()

        def worker(*_):
            entered.set()
            release.wait(3)
            raise HTTPException(502, "original model failure")

        async def check():
            ticks = 0
            stopped = asyncio.Event()

            async def heartbeat():
                nonlocal ticks
                while not stopped.is_set():
                    ticks += 1
                    await asyncio.sleep(0.005)

            with patch.object(deps.turns, "execute", side_effect=worker):
                TurnRequests(deps.settings.db_path).begin("s", "r", "hash")
                task = asyncio.create_task(deps.turns.aexecute(TurnRequest(text="hello"), "s", "r"))
                while not entered.is_set():
                    await asyncio.sleep(0.005)
                conn = sqlite3.connect(deps.settings.db_path, check_same_thread=False)
                conn.execute("BEGIN IMMEDIATE")

                def unlock():
                    conn.rollback()
                    conn.close()
                    release.set()

                timer = threading.Timer(0.15, unlock)
                timer.start()
                beat = asyncio.create_task(heartbeat())
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
                stopped.set()
                await beat
                timer.join()
                self.assertGreater(ticks, 8)
            release.clear()
            entered.clear()
            with (
                patch.object(deps.turns, "execute", side_effect=worker),
                patch.object(deps.turns, "cancel", side_effect=OSError("busy")),
                self.assertLogs("modules.chat_api.service", level="ERROR"),
            ):
                task = asyncio.create_task(deps.turns.aexecute(TurnRequest(text="hello"), "s", "other"))
                while not entered.is_set():
                    await asyncio.sleep(0.005)
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
                release.set()

        asyncio.run(check())


class ProcessPolicyTests(unittest.TestCase):
    def test_old_record_and_reused_pid_never_authorize_termination(self):
        self.assertEqual(members({"pgid": 123, "token": "old"}), [])
        fake = MagicMock()
        fake.create_time.return_value = 500
        with (
            patch("infrastructure.processes.psutil.Process", return_value=fake),
            patch("infrastructure.processes.psutil.process_iter") as scan,
        ):
            self.assertEqual(
                members(
                    {"version": 1, "pid": 123, "created_at": 100, "token": "token", "project": "project"}
                ),
                [],
            )
            scan.assert_not_called()

    def test_windows_stop_delegates_ownership_and_does_not_kill_by_port_or_name(self):
        import launcher.stack as launcher

        root = Path("C:/test/project")
        with (
            patch.object(launcher, "stop_owned") as owned,
            patch.object(launcher, "wsl_distro", return_value=None),
            patch.object(launcher.subprocess, "run") as run,
        ):
            launcher.stop_stack(root, {"frontend", "backend"})
            self.assertEqual(owned.call_count, 2)
            run.assert_not_called()
        for path in ("launcher/stack.py", "scripts/dev_stack.ps1"):
            source = Path(path).read_text()
            self.assertNotIn("pkill -f", source)
            self.assertNotIn("taskkill", source)


if __name__ == "__main__":
    unittest.main()
