"""Independent browser cases with fresh contexts, simulated APIs and microphone.

Run all: python scripts/check_frontend_interactions.py
Run one: python scripts/check_frontend_interactions.py --case test_timeout
"""
import argparse
import asyncio
import json
import unittest
from playwright.async_api import async_playwright, expect, Error as BrowserError


class BrowserCases(unittest.IsolatedAsyncioTestCase):
    base_url = "http://127.0.0.1:3000"

    async def asyncSetUp(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch()
        self.page = await self.browser.new_page()
        self.addAsyncCleanup(self.playwright.stop)
        self.addAsyncCleanup(self.browser.close)
        await self.page.add_init_script("""
            localStorage.setItem('ax-user-local-id', 'interaction-check');
            localStorage.setItem('bina-live2d-model', '');
            localStorage.setItem('ax-solo-conversations-v1:interaction-check', JSON.stringify({
                activeId: 'check-a', items: ['a', 'b'].map(id => ({
                    id: 'check-' + id, title: 'Conversation ' + id,
                    preview: '', updatedAt: '2026-01-01T00:00:00Z'
                }))
            }));
            window.SpeechRecognition = undefined;
            window.webkitSpeechRecognition = undefined;
            window.previewCreated = 0;
            window.previewRevoked = 0;
            const create = URL.createObjectURL.bind(URL);
            const revoke = URL.revokeObjectURL.bind(URL);
            URL.createObjectURL = (...args) => { window.previewCreated++; return create(...args); };
            URL.revokeObjectURL = (...args) => { window.previewRevoked++; return revoke(...args); };
            window.stoppedTracks = 0;
            navigator.mediaDevices.getUserMedia = async () => ({
                getTracks: () => [{ stop: () => window.stoppedTracks++ }]
            });
            window.MediaRecorder = class {
                static isTypeSupported() { return true; }
                state = 'inactive';
                mimeType = 'audio/webm';
                start() { this.state = 'recording'; }
                stop() {
                    this.state = 'inactive';
                    queueMicrotask(() => {
                        this.ondataavailable?.({ data: new Blob(['x'.repeat(300)]) });
                        this.onstop?.();
                    });
                }
            };
        """)
        self.old_history_started = asyncio.Event()
        self.release_old_history = asyncio.Event()
        self.refreshed_history_started = asyncio.Event()
        self.release_refreshed_history = asyncio.Event()
        self.chat_started = asyncio.Event()
        self.release_chat = asyncio.Event()
        self.transcription_started = asyncio.Event()
        self.release_transcription = asyncio.Event()
        self.history_count = 0
        self.stt_count = 0
        self.upload_started = asyncio.Event()
        self.release_upload = asyncio.Event()
        self.hold_upload = True
        self.upload_error = False
        self.sent_bodies = []
        self.cancel_status = "cancelled"
        self.hold_refresh = False
        self.hold_transcription = False

        self.hold_initial = False
        self.release_chat.set()
        await self.page.route("**/api/**", self.api)
        for attempt in range(50):
            try:
                await self.page.goto(f"{self.base_url.rstrip('/')}/solo")
                break
            except BrowserError as exc:
                if "ERR_CONNECTION_REFUSED" not in str(exc) or attempt == 49:
                    raise
                await asyncio.sleep(.2)
        self.subtitle = self.page.locator(".bina-subtitle")
        self.textbox = self.page.get_by_role("textbox", name="对 Bina 说")
        await expect(self.subtitle).to_have_text("History check-a")

    async def asyncTearDown(self):
        for name, value in vars(self).items():
            if name.startswith('release_'):
                value.set()

    async def api(self, route):
        path = route.request.url.split("?", 1)[0]
        data = {"ok": True}
        if path.endswith("/personas/bina"):
            data = {"id": "bina", "name": "Bina", "greeting": "Greeting", "color": "#aaaaaa"}
        elif path.endswith("/chat/options"):
            data = {"models": ["mock"], "default_model": "mock", "reasoning_levels": []}
        elif path.endswith("/chat/history"):
            self.history_count += 1
            sid = route.request.headers.get("x-session-id")
            if sid == "check-a" and self.hold_initial:
                self.old_history_started.set()
                await self.release_old_history.wait()
            elif self.hold_refresh:
                self.refreshed_history_started.set()
                await self.release_refreshed_history.wait()
            data = {"turns": [{"user": "hello", "assistant": f"History {sid}", "ts": ""}]}
        elif path.endswith("/attachments/ingest"):
            self.upload_started.set()
            if self.hold_upload:
                await self.release_upload.wait()
            if self.upload_error:
                await route.fulfill(status=500, content_type="application/json", body='{"detail":"Old upload error"}')
                return
            data = {"name": "old.png", "kind": "image", "text": "PRIVATE OLD ATTACHMENT", "truncated": False}
        elif path.endswith("/cancel"):
            data = {"status": self.cancel_status}
        elif "/chat/requests/" in path:
            data = {"status": "completed", "result": {"reply": "Saved reply", "active_persona": "bina"}}
        elif path.endswith("/v1/chat"):
            self.sent_bodies.append(route.request.post_data_json)
            self.chat_started.set()
            await self.release_chat.wait()
            data = {"reply": "Fresh reply", "active_persona": "bina"}
        elif path.endswith("/stt"):
            self.stt_count += 1
            self.transcription_started.set()
            if self.hold_transcription:
                await self.release_transcription.wait()
            data = {"text": "Recognized speech"}
        await route.fulfill(content_type="application/json", body=json.dumps(data))


    async def send(self, text="New message"):
        self.chat_started.clear()
        await self.textbox.fill(text)
        await self.page.get_by_role("button", name="发送", exact=True).click()
        await asyncio.wait_for(self.chat_started.wait(), 5)

    async def stop(self):
        await self.page.get_by_role("button", name="停止", exact=True).click()

    async def test_stale_history(self):
        self.hold_initial = True
        await self.page.evaluate("window.dispatchEvent(new Event('focus'))")
        await asyncio.wait_for(self.old_history_started.wait(), 5)
        await self.page.get_by_title("谈话列表").click()
        await self.page.get_by_role("button", name="Conversation b").click()
        await expect(self.subtitle).to_have_text("History check-b")
        self.release_old_history.set()
        await self.page.wait_for_timeout(100)
        await expect(self.subtitle).to_have_text("History check-b")

    async def test_history_during_send(self):
        self.hold_refresh = True
        await self.page.evaluate("window.dispatchEvent(new Event('focus'))")
        await asyncio.wait_for(self.refreshed_history_started.wait(), 5)
        self.release_chat.clear()
        await self.send()
        self.release_refreshed_history.set()
        await expect(self.subtitle).to_have_attribute("aria-busy", "true")
        count = self.history_count
        await self.page.evaluate("window.dispatchEvent(new Event('focus'))")
        await self.page.wait_for_timeout(100)
        self.assertEqual(self.history_count, count)
        self.release_chat.set()
        await expect(self.subtitle).to_have_text("Fresh reply")

    async def record(self):
        await self.page.get_by_role("button", name="服务端识别", exact=True).click()
        await expect(self.page.get_by_role("button", name="结束录音", exact=True)).to_be_visible()

    async def test_record_cancel(self):
        await self.record()
        await self.stop()
        await self.page.wait_for_timeout(100)
        self.assertEqual(self.stt_count, 0)
        self.assertEqual(await self.page.evaluate("window.stoppedTracks"), 1)

    async def test_record_finish(self):
        await self.record()
        await self.page.get_by_role("button", name="结束录音", exact=True).click()
        await expect(self.textbox).to_have_value("Recognized speech")
        self.assertEqual(self.stt_count, 1)

    async def test_transcription_late(self):
        self.hold_transcription = True
        await self.record()
        await self.page.get_by_role("button", name="结束录音", exact=True).click()
        await asyncio.wait_for(self.transcription_started.wait(), 5)
        await self.stop()
        self.release_transcription.set()
        await self.page.wait_for_timeout(100)
        await expect(self.textbox).to_have_value("")
        await expect(self.textbox).to_be_enabled()

    async def stop_case(self, status):
        self.cancel_status = status
        self.release_chat.clear()
        await self.send(f"Stop case {status}")
        request_id = self.sent_bodies[-1]['request_id']
        await self.stop()
        if status == 'completed':
            await expect(self.subtitle).to_have_text('Saved reply')
        else:
            await expect(self.page.get_by_role('alert').filter(has_text='此回合')).to_be_visible()
        await expect(self.textbox).to_be_enabled()
        self.release_chat.set()
        if status != 'completed':
            await self.page.get_by_role('button', name='发送', exact=True).click()
            await expect(self.subtitle).to_have_text('Fresh reply')
            self.assertEqual(self.sent_bodies[-1]['request_id'] == request_id, status == 'committing')

    async def test_stop_cancelled(self):
        await self.stop_case('cancelled')

    async def test_stop_committing(self):
        await self.stop_case('committing')

    async def test_stop_completed(self):
        await self.stop_case('completed')

    async def test_timeout(self):
        self.release_chat.clear()
        await self.page.evaluate("""window.originalSetTimeout = window.setTimeout;
            window.setTimeout = (fn, ms, ...args) => window.originalSetTimeout(fn, ms === 120000 ? 100 : ms, ...args);""")
        await self.send('Timeout case')
        await expect(self.page.get_by_text('此回合已取消，未保存对话。', exact=True)).to_be_visible()
        await expect(self.textbox).to_be_enabled()

    async def upload(self):
        self.upload_started.clear()
        self.release_upload.clear()
        await self.page.locator('input[type="file"]').set_input_files({
            'name': 'old.png', 'mimeType': 'image/png', 'buffer': b'fake image'})
        await asyncio.wait_for(self.upload_started.wait(), 5)

    async def upload_case(self, action):
        self.upload_error = action == 'create'
        await self.upload()
        await self.page.get_by_title('谈话列表').click()
        if action == 'switch':
            await self.page.get_by_role('button', name='Conversation b').click()
        elif action == 'create':
            await self.page.get_by_role('button', name='新建谈话', exact=True).click()
        else:
            self.page.once('dialog', lambda dialog: dialog.accept())
            row = self.page.locator('.ax-convo-panel li').filter(has=self.page.get_by_role('button', name='Conversation a'))
            await row.get_by_role('button', name='结束', exact=True).click()
            await self.page.get_by_title('谈话列表').click()
        self.release_upload.set()
        await self.page.wait_for_timeout(100)
        await expect(self.page.get_by_role('button', name='附件', exact=True)).to_be_enabled()
        await expect(self.page.get_by_text('图片 · old.png', exact=True)).to_have_count(0)
        await expect(self.page.get_by_text('Old upload error', exact=True)).to_have_count(0)
        self.assertEqual(await self.page.evaluate('window.previewCreated'), 0)
        await self.send('No leaked attachment')
        await expect(self.subtitle).to_have_text('Fresh reply')
        self.assertEqual(self.sent_bodies[-1]['text'], 'No leaked attachment')

    async def test_upload_switch(self):
        await self.upload_case('switch')

    async def test_upload_create(self):
        await self.upload_case('create')

    async def test_upload_remove(self):
        await self.upload_case('remove')

    async def test_preview_cleanup_and_unmount(self):
        self.hold_upload = False
        await self.upload()
        await expect(self.page.get_by_text('图片 · old.png', exact=True)).to_be_visible()
        await self.page.get_by_title('谈话列表').click()
        await self.page.get_by_role('button', name='新建谈话', exact=True).click()
        self.assertEqual(await self.page.evaluate('window.previewRevoked'), 1)
        self.hold_upload = True
        await self.upload()
        await self.page.goto('about:blank')
        self.release_upload.set()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default=BrowserCases.base_url)
    parser.add_argument('--case', help='Run one named case (e.g. test_timeout)')
    args = parser.parse_args()
    BrowserCases.base_url = args.base_url
    suite = unittest.defaultTestLoader.loadTestsFromName(args.case, BrowserCases) if args.case else unittest.defaultTestLoader.loadTestsFromTestCase(BrowserCases)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
