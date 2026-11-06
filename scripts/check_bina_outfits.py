"""Verify real casual/work Live2D loading, outfit persistence and motion previews."""

import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
WORK = "/live2d/bina-work/bina.model3.json"
CASUAL = "/live2d/bina-registered/bina.model3.json"


def check(base_url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=[
            "--no-sandbox", "--enable-unsafe-swiftshader", "--use-gl=angle",
            "--use-angle=swiftshader", "--ozone-platform=headless",
        ])
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        errors = []
        resources = []
        actions = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("response", lambda response: resources.append({
            "path": response.url.split("/live2d/", 1)[-1], "status": response.status,
        }) if "/live2d/bina-work/" in response.url else None)

        def ready(outfit):
            expect(page.locator(".bina-scene-footer")).to_contain_text(f"BINA · {outfit}形象")
            page.wait_for_function(
                "document.querySelector('.bina-scene-footer')?.textContent.endsWith('Live2D')",
                timeout=30000,
            )

        page.goto(base_url.rstrip("/") + "/solo", wait_until="domcontentloaded")
        ready("日常")
        page.get_by_role("tab", name="形象", exact=True).click()
        page.get_by_role("button", name="工装", exact=True).click()
        ready("工装")
        expect(page.get_by_role("button", name="工装", exact=True)).to_have_attribute("aria-pressed", "true")
        assert page.evaluate("localStorage.getItem('bina-live2d-model')") == WORK
        page.screenshot(path=str(ROOT / "assets/bina-live2d/work-browser-desktop.png"), full_page=True)
        for name in ("Blink", "Nod", "Shake", "Smile", "Sad", "Angry", "Surprised"):
            page.get_by_role("button", name=name, exact=True).click()
            page.wait_for_timeout(500)
            page.locator(".bina-live2d").screenshot(path=str(ROOT / f".devstack/work-action-{name}.png"))
            actions.append(name)
        page.reload(wait_until="domcontentloaded")
        ready("工装")
        assert page.evaluate("localStorage.getItem('bina-live2d-model')") == WORK
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)
        page.screenshot(path=str(ROOT / "assets/bina-live2d/work-browser-mobile.png"), full_page=True)
        page.get_by_role("tab", name="形象", exact=True).click()
        page.get_by_role("button", name="日常装", exact=True).click()
        ready("日常")
        assert page.evaluate("localStorage.getItem('bina-live2d-model')") == CASUAL
        page.get_by_role("button", name="工装", exact=True).click()
        ready("工装")
        page.wait_for_timeout(300)
        report = {
            "model": WORK, "base_url": base_url, "outfit": "work", "pose": "standing",
            "casual_to_work": True, "work_to_casual": True, "refresh_preserved": True,
            "mobile_rendered": True, "actions": actions, "page_errors": errors,
            "resources": resources, "limitations": ["No independent arm gestures or lip sync"],
        }
        (ROOT / "assets/bina-live2d/work-browser-verification.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        assert resources and all(item["status"] == 200 for item in resources), resources
        assert not errors, errors
        browser.close()
        print("PASS: casual/work switching, persisted outfit, seven previews and mobile rendering")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:3000")
    check(parser.parse_args().base_url)
