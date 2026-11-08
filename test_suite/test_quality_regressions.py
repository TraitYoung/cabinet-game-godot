"""Regression coverage for Q01–Q09; all chat/memory calls use fakes and temporary data."""
import asyncio
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import importlib.util
import json
import os
import shutil
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from fastapi import HTTPException

import modules.chat_api.routes as main
from app.factory import create_app
from config.settings import Settings
from infrastructure.container import Container
from agents.solo_fast import synthesize_solo_bina_intent
from memory.context_inject import compose_user_message
from modules.chat_api.service import TurnRequest, TurnResult, TurnService
from state.mood_engine import MoodEngine
from storage.chat_history import ChatHistory
from storage.turn_requests import TurnRequests


class TurnLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = str(Path(self.directory.name) / 'chat.db')
        self.history = ChatHistory(self.path)
        self.container = Container(Settings(db_path=self.path, proactive_enabled=False))
        self.container.history = self.history
        from unittest.mock import MagicMock
        self.memory = MagicMock()
        self.container.memory = self.memory
        self.svc = self.container.turns
        self.payload = TurnRequest(text='hello', memory_thread_id='test-user')
        self.result = TurnResult(reply='reply', intent=synthesize_solo_bina_intent('hello'), trace_raw=[], active_task_type='chat', active_persona='bina')

    def test_cancel_generation_and_immediate_retry_cannot_commit(self):
        entered, release = threading.Event(), threading.Event()
        def generate(*_):
            entered.set()
            self.assertTrue(release.wait(3))
            return self.result
        with patch.object(self.svc, 'run', side_effect=generate), ThreadPoolExecutor() as pool:
            future = pool.submit(self.svc.execute, self.payload, 'a', 'request')
            self.assertTrue(entered.wait(2))
            self.assertEqual(self.svc.cancel('a', 'request')['status'], 'cancelled')
            with self.assertRaises(HTTPException) as error:
                self.svc.execute(self.payload, 'a', 'retry')
            self.assertEqual(error.exception.status_code, 409)
            release.set()
            with self.assertRaises(HTTPException):
                future.result(3)
        self.assertEqual(self.history.get_turns('a'), [])
        self.memory.retain_turn.assert_not_called()

    def test_cancel_before_request_arrives_prevents_generation(self):
        self.svc.cancel('a', 'request')
        with patch.object(self.svc, 'run') as generate, self.assertRaises(HTTPException):
            self.svc.execute(self.payload, 'a', 'request')
        generate.assert_not_called()

    def test_commit_is_not_cancelled_and_retries_reuse_saved_result(self):
        entered, release = threading.Event(), threading.Event()
        def retain(*_, **__):
            entered.set()
            self.assertTrue(release.wait(3))
            raise RuntimeError('temporary memory failure')
        self.memory.retain_turn.side_effect = retain
        with patch.object(self.svc, 'run', return_value=self.result) as generate, ThreadPoolExecutor() as pool:
            future = pool.submit(self.svc.execute, self.payload, 'a', 'request')
            self.assertTrue(entered.wait(2))
            self.assertEqual(self.svc.cancel('a', 'request')['status'], 'committing')
            release.set()
            with self.assertRaises(HTTPException):
                future.result(3)
            first = self.memory.retain_turn.call_args
            self.memory.retain_turn.side_effect = None
            # Simulate a restarted service resuming the durable prepared result.
            self.assertEqual(TurnService(self.container).execute(self.payload, 'a', 'request').reply, 'reply')
            self.assertEqual(first, self.memory.retain_turn.call_args)
            self.svc.execute(self.payload, 'a', 'request')
            generate.assert_called_once()
        self.assertEqual(len(self.history.get_turns('a')), 1)
        self.assertEqual(self.memory.retain_turn.call_count, 2)
        self.assertEqual(self.svc.request_status('a', 'request')['status'], 'completed')
        with self.assertRaises(HTTPException):
            self.svc.execute(TurnRequest(text='changed'), 'a', 'request')

    def test_same_session_sees_previous_commit_and_other_sessions_can_run(self):
        entered, release = threading.Event(), threading.Event()
        snapshots = []
        def generate(payload, session):
            snapshots.append((session, self.history.get_turns(session)))
            if session == 'a' and payload.text == 'hello':
                entered.set()
                self.assertTrue(release.wait(3))
            return self.result
        with patch.object(self.svc, 'run', side_effect=generate), ThreadPoolExecutor() as pool:
            first = pool.submit(self.svc.execute, self.payload, 'a', 'first')
            self.assertTrue(entered.wait(2))
            self.svc.execute(self.payload, 'b', 'parallel')
            with self.assertRaises(HTTPException):
                TurnService(self.container).execute(self.payload, 'a', 'second')
            release.set()
            first.result(3)
            self.svc.execute(TurnRequest(text='next'), 'a', 'second')
        self.assertEqual(len(snapshots[-1][1]), 1)
        self.assertEqual([turn['user'] for turn in self.history.get_turns('a')], ['hello', 'next'])

    def test_disconnected_http_wait_cancels_worker_before_commit(self):
        entered, release = threading.Event(), threading.Event()
        def generate(*_):
            entered.set()
            release.wait(3)
            return self.result
        async def check():
            with patch.object(self.svc, 'run', side_effect=generate):
                task = asyncio.create_task(main._await_turn(self.svc, main.ChatRequest(text='hello', request_id='disconnect'), 'a', 'test-user'))
                while not entered.is_set():
                    await asyncio.sleep(.01)
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
                release.set()
        asyncio.run(check())  # also waits for the worker to finish
        self.assertEqual(self.history.get_turns('a'), [])
        self.memory.retain_turn.assert_not_called()

    def test_adapter_cancellation_uses_the_same_commit_boundary(self):
        from modules.chat_api.adapter import ChatAdapter
        entered, release = threading.Event(), threading.Event()
        def generate(*_):
            entered.set()
            release.wait(3)
            return self.result
        async def check():
            with patch.object(self.svc, 'run', side_effect=generate):
                task = asyncio.create_task(ChatAdapter(self.svc).stream('hello', session_id='a'))
                while not entered.is_set():
                    await asyncio.sleep(.01)
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task
                release.set()
        asyncio.run(check())
        self.assertEqual(self.history.get_turns('a'), [])
        self.memory.retain_turn.assert_not_called()

    def test_session_exclusion_works_across_processes(self):
        code = """import sys
from storage.turn_requests import TurnRequests
from fastapi import HTTPException
try:
    with TurnRequests(sys.argv[1]).session('a'):
        raise SystemExit(1)
except HTTPException as exc:
    assert exc.status_code == 409
"""
        with TurnRequests(self.path).session('a'):
            child = subprocess.run([sys.executable, '-c', code, self.path], capture_output=True, timeout=10)
            self.assertEqual(child.returncode, 0, child.stderr.decode())

    def test_sse_disconnect_cancels_generation_before_commit(self):
        entered, release = threading.Event(), threading.Event()
        def generate(*_):
            entered.set()
            release.wait(4)
            return self.result
        async def check():
            with patch.object(self.svc, 'run', side_effect=generate):
                response = await main.chat_stream_api(
                    main.ChatRequest(text='hello', request_id='stream-disconnect'), None,
                    x_session_id='a', x_trace_id=None, x_memory_thread='test-user', service=self.svc)
                iterator = response.body_iterator
                await anext(iterator)
                await anext(iterator)  # next heartbeat while the worker is blocked
                self.assertTrue(entered.is_set())
                await iterator.aclose()
                release.set()
        asyncio.run(check())
        self.assertEqual(self.history.get_turns('a'), [])
        self.memory.retain_turn.assert_not_called()


class MoodRegressionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = str(Path(self.directory.name) / 'mood.db')
        self.engine = MoodEngine(self.path)

    def test_idle_ticks_preserve_reunion_and_daily_first_interaction(self):
        start = datetime(2026, 11, 6, 15)
        self.engine.arm_interaction_hook('a', start)
        for minutes in (30, 60, 120, 180):
            self.engine.tick_idle('a', start + timedelta(minutes=minutes))
        self.assertIn('两小时', self.engine.arm_interaction_hook('a', start + timedelta(hours=3)))
        self.assertEqual(self.engine.arm_interaction_hook('a', start + timedelta(hours=3)), '')
        tomorrow = start + timedelta(days=1)
        self.engine.tick_idle('a', tomorrow)
        self.assertIn('今日首次', self.engine.arm_interaction_hook('a', tomorrow))
        self.assertEqual(self.engine.arm_interaction_hook('a', tomorrow), '')
        self.engine.tick_idle('new', tomorrow)
        self.assertIn('首次交互', self.engine.arm_interaction_hook('new', tomorrow))

    def test_concurrent_updates_across_instances_preserve_deltas_and_bounds(self):
        other = MoodEngine(self.path)
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(lambda i: (self.engine if i % 2 else other).apply_delta('a', valence=.02), range(20)))
        self.assertAlmostEqual(self.engine.get_state('a').valence, .4)
        now = datetime(2026, 11, 7, 15)
        self.engine.tick_idle('a', now)
        before = self.engine.get_state('a').valence
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(other.tick_idle, 'a', now), pool.submit(self.engine.reset_connection, 'a'),
                       pool.submit(other.apply_delta, 'a', valence=.2, arousal=10)]
            for future in futures:
                future.result()
        state = self.engine.get_state('a')
        self.assertAlmostEqual(state.valence, before + .2)
        self.assertEqual(state.arousal, 1)
        self.assertEqual(state.connection, 0)

    def test_legacy_schema_migrates_last_interaction_once(self):
        legacy = str(Path(self.directory.name) / 'legacy.db')
        with closing(sqlite3.connect(legacy)) as conn, conn:
            conn.execute('CREATE TABLE mood_state (thread_id TEXT PRIMARY KEY, connection REAL, pride REAL, valence REAL, arousal REAL, immersion REAL, last_tick_at TEXT)')
            conn.execute("INSERT INTO mood_state VALUES ('a',0,0,0,0,.3,'2026-11-06T12:00:00')")
        engine = MoodEngine(legacy)
        engine.tick_idle('a', datetime(2026, 11, 6, 15))
        self.assertIn('两小时', MoodEngine(legacy).compute_interaction_hook('a', datetime(2026, 11, 6, 15)))


class HistoryBudgetTests(unittest.TestCase):
    def test_long_messages_and_attachments_keep_both_speakers_within_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            history = ChatHistory(str(Path(directory) / 'history.db'))
            for i in range(7):
                history.append_turn('a', f'user{i} \nBina: quoted speaker in attachment\n' + '附件' * 3000, f'answer{i} ' + 'reply' * 3000)
            prompt = compose_user_message('current', recent_history=history.format_for_prompt('a'))
        self.assertLess(len(prompt), 4000)
        for i in range(2, 7):
            self.assertIn(f'User: user{i}', prompt)
            self.assertIn(f'Bina: answer{i}', prompt)
        self.assertNotIn('answer1', prompt)


class LauncherTests(unittest.TestCase):
    def test_stop_preserves_other_project_and_rejects_stale_ownership(self):
        spec = importlib.util.spec_from_file_location('stack_process', 'scripts/stack_process.py')
        launcher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(launcher)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            own, other = root / 'own.json', root / 'other.json'
            command = ['bash', '-c', 'exec -a next-server "$@"', 'bina-test', sys.executable, '-c', 'import time; time.sleep(60)']
            own_process = launcher.start(own, root, root / 'own.log', command)
            other_process = launcher.start(other, root, root / 'other.log', command)
            try:
                record = json.loads(other.read_text())
                stale = root / 'stale.json'
                stale.write_text(json.dumps({**record, 'token': 'expired'}))
                launcher.stop(stale)
                self.assertTrue(launcher.members(record))
                own_record = json.loads(own.read_text())
                launcher.stop(own)
                self.assertFalse(launcher.members(own_record))
                self.assertTrue(launcher.members(record))
            finally:
                launcher.stop(own)
                launcher.stop(other)
                own_process.wait(timeout=3)
                other_process.wait(timeout=3)

    def test_stop_script_ignores_stale_pid_and_foreign_port(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            (root / '.devstack').mkdir()
            (root / 'bin').mkdir()
            shutil.copytree('infrastructure', root / 'infrastructure')
            (root / '.venv/bin').mkdir(parents=True)
            (root / '.venv/bin/python').symlink_to(sys.executable)
            for name in ('dev_stack.sh', 'stack_process.py'):
                shutil.copyfile(Path('scripts') / name, root / 'scripts' / name)
            # A foreign toolchain owns the port; the stop command must never use it as ownership proof.
            foreign = subprocess.Popen(['bash', '-c', 'exec -a next-server "$@"', 'bina-test', sys.executable,
                                        '-c', 'import time; time.sleep(60)'], start_new_session=True)
            try:
                (root / '.devstack/backend.json').write_text(json.dumps({'pgid': foreign.pid, 'token': 'expired'}))
                for name, body in {
                    'docker': '#!/bin/sh\nexit 0\n',
                    'ss': '#!/bin/sh\nprintf "State Recv-Q Send-Q Local Address:Port Peer Address:Port\nLISTEN 0 1 127.0.0.1:3000 0.0.0.0:*\n"\n',
                }.items():
                    command = root / 'bin' / name
                    command.write_text(body)
                    command.chmod(0o755)
                result = subprocess.run(['bash', str(root / 'scripts/dev_stack.sh'), 'stop'],
                    env={**os.environ, 'PATH': str(root / 'bin') + ':' + os.environ['PATH'],
                         'NVM_DIR': directory, 'PYTHONPATH': os.pathsep.join(sys.path), 'AX_DB_PATH': str(root / 'test.db')},
                    capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr.decode())
                self.assertIsNone(foreign.poll())
            finally:
                foreign.terminate()
                foreign.wait(timeout=3)

    def test_compose_local_bindings_and_container_database_override(self):
        config = json.loads(subprocess.check_output(['docker', 'compose', 'config', '--format', 'json']))
        api = config['services']['api']
        db_path = api['environment']['AX_DB_PATH']
        volume = next(item for item in api['volumes'] if item['target'] == str(Path(db_path).parent))
        self.assertEqual(volume['type'], 'volume')
        self.assertEqual(volume['source'], 'api-data')
        for service in config['services'].values():
            for port in service.get('ports', []):
                self.assertEqual(port['host_ip'], '127.0.0.1')


if __name__ == '__main__':
    unittest.main()
