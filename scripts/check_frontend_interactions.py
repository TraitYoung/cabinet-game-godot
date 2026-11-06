"""Browser regression checks with mocked APIs and microphone; no model calls."""

import argparse
import asyncio
import json

from playwright.async_api import async_playwright, expect


async def check(base_url: str) -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        page = await browser.new_page()
        await page.add_init_script("""
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
        old_history_started = asyncio.Event()
        release_old_history = asyncio.Event()
        refreshed_history_started = asyncio.Event()
        release_refreshed_history = asyncio.Event()
        chat_started = asyncio.Event()
        release_chat = asyncio.Event()
        transcription_started = asyncio.Event()
        release_transcription = asyncio.Event()
        history_count = 0
        stt_count = 0
        hold_refresh = False
        hold_transcription = False

        async def api(route):
            nonlocal history_count, stt_count
            path = route.request.url.split("?", 1)[0]
            data = {"ok": True}
            if path.endswith("/personas/bina"):
                data = {"id": "bina", "name": "Bina", "greeting": "Greeting", "color": "#aaaaaa"}
            elif path.endswith("/chat/options"):
                data = {"models": ["mock"], "default_model": "mock", "reasoning_levels": []}
            elif path.endswith("/chat/history"):
                history_count += 1
                sid = route.request.headers.get("x-session-id")
                if sid == "check-a":
                    old_history_started.set()
                    await release_old_history.wait()
                elif hold_refresh:
                    refreshed_history_started.set()
                    await release_refreshed_history.wait()
                data = {"turns": [{"user": "hello", "assistant": f"History {sid}", "ts": ""}]}
            elif path.endswith("/v1/chat"):
                chat_started.set()
                await release_chat.wait()
                data = {"reply": "Fresh reply", "active_persona": "bina"}
            elif path.endswith("/stt"):
                stt_count += 1
                transcription_started.set()
                if hold_transcription:
                    await release_transcription.wait()
                data = {"text": "Recognized speech"}
            await route.fulfill(content_type="application/json", body=json.dumps(data))

        await page.route("**/api/**", api)
        try:
            await page.goto(f"{base_url.rstrip('/')}/solo")
            await asyncio.wait_for(old_history_started.wait(), 30)
            await page.get_by_title("谈话列表").click()
            await page.get_by_role("button", name="Conversation b").click()
            subtitle = page.locator(".bina-subtitle")
            await expect(subtitle).to_have_text("History check-b")
            release_old_history.set()
            await page.wait_for_timeout(150)
            await expect(subtitle).to_have_text("History check-b")
            print("PASS: stale conversation history cannot replace the current conversation")

            hold_refresh = True
            await page.evaluate("window.dispatchEvent(new Event('focus'))")
            await asyncio.wait_for(refreshed_history_started.wait(), 5)
            await page.get_by_role("textbox", name="对 Bina 说").fill("New message")
            await page.get_by_role("button", name="发送", exact=True).click()
            await asyncio.wait_for(chat_started.wait(), 5)
            release_refreshed_history.set()
            await page.wait_for_timeout(150)
            await expect(subtitle).to_have_attribute("aria-busy", "true")
            assert await subtitle.inner_text() != "History check-b"
            count_before_focus = history_count
            await page.evaluate("window.dispatchEvent(new Event('focus'))")
            await page.wait_for_timeout(150)
            assert history_count == count_before_focus
            release_chat.set()
            await expect(subtitle).to_have_text("Fresh reply")
            print("PASS: history refresh preserves the pending reply and skips focus refresh while sending")

            await page.get_by_role("button", name="服务端识别", exact=True).click()
            await expect(page.get_by_role("button", name="结束录音", exact=True)).to_be_visible()
            await page.get_by_role("button", name="停止", exact=True).click()
            await page.wait_for_timeout(150)
            assert stt_count == 0
            assert await page.evaluate("window.stoppedTracks") == 1
            print("PASS: cancelling a recording stops its microphone without uploading")

            await page.get_by_role("button", name="服务端识别", exact=True).click()
            await page.get_by_role("button", name="结束录音", exact=True).click()
            textbox = page.get_by_role("textbox", name="对 Bina 说")
            await expect(textbox).to_have_value("Recognized speech")
            assert stt_count == 1
            print("PASS: finishing a recording still transcribes normally")

            await textbox.fill("")
            hold_transcription = True
            transcription_started.clear()
            await page.get_by_role("button", name="服务端识别", exact=True).click()
            await page.get_by_role("button", name="结束录音", exact=True).click()
            await asyncio.wait_for(transcription_started.wait(), 5)
            await page.get_by_role("button", name="停止", exact=True).click()
            release_transcription.set()
            await page.wait_for_timeout(150)
            await expect(textbox).to_have_value("")
            await expect(textbox).to_be_enabled()
            print("PASS: cancelling transcription ignores late results")
        finally:
            release_old_history.set()
            release_refreshed_history.set()
            release_chat.set()
            release_transcription.set()
            await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:3000")
    asyncio.run(check(parser.parse_args().base_url))
