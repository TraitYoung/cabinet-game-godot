import test from "node:test";
import assert from "node:assert/strict";
import { proxyJson } from "../src/infra/proxy.ts";
import { apiFetch, ApiError } from "../src/matrix/http.ts";

for (const status of [400, 409, 422, 503]) {
  test(`proxy preserves backend ${status}, browser parses its error`, async (context) => {
    context.mock.method(globalThis, "fetch", async () => Response.json({ code: "sample_code", detail: "清晰错误" }, { status }));
    const request = new Request("http://frontend/api/chat/history?limit=7", { headers: { "x-session-id": "session" } });
    const response = await proxyJson(request, "/api/v1/chat/history", { requireSession: true });
    assert.equal(response.status, status);
    context.mock.restoreAll();
    context.mock.method(globalThis, "fetch", async () => response);
    await assert.rejects(() => apiFetch("http://frontend"), (error: unknown) => {
      assert.ok(error instanceof ApiError); assert.equal(error.status, status);
      assert.equal(error.code, "sample_code"); assert.equal(error.message, "清晰错误"); return true;
    });
  });
}
test("history limit, identity, request body and cancellation reach the backend", async (context) => {
  let captured: { url: string; init?: RequestInit } | undefined;
  context.mock.method(globalThis, "fetch", async (url: RequestInfo | URL, init?: RequestInit) => { captured = { url: String(url), init }; return Response.json({ turns: [] }); });
  const request = new Request("http://frontend/api/chat/history?limit=7", { headers: { "x-session-id": "session" } });
  await proxyJson(request, "/api/v1/chat/history", { requireSession: true });
  assert.ok(captured?.url.endsWith("/api/v1/chat/history?limit=7"));
  assert.equal(new Headers(captured?.init?.headers).get("x-session-id"), "session");
  assert.ok(captured?.init?.signal);
});
test("missing session and invalid backend JSON have explicit errors", async (context) => {
  assert.equal((await proxyJson(new Request("http://frontend/"), "/history", { requireSession: true })).status, 400);
  context.mock.method(globalThis, "fetch", async () => new Response("not JSON"));
  assert.equal((await proxyJson(new Request("http://frontend/"), "/history")).status, 502);
});
test("network failure is distinct from backend status", async (context) => {
  context.mock.method(globalThis, "fetch", async () => { throw new Error("connection refused"); });
  const response = await proxyJson(new Request("http://frontend/"), "/health");
  assert.equal(response.status, 503); assert.equal((await response.json()).code, "backend_unavailable");
});

test("body is forwarded and timeout/cancellation are distinguishable", async (context) => {
  let body: BodyInit | null | undefined;
  context.mock.method(globalThis, "fetch", async (_url: RequestInfo | URL, init?: RequestInit) => { body = init?.body; return Response.json({ ok: true }); });
  await proxyJson(new Request("http://frontend/api/presence", { method: "POST", body: '{"session_id":"s"}' }), "/api/v1/presence", { forwardBody: true });
  assert.equal(body, '{"session_id":"s"}');
  context.mock.restoreAll();
  context.mock.method(globalThis, "fetch", async () => {
    await new Promise((resolve) => setTimeout(resolve, 15));
    throw new Error("aborted transport");
  });
  const timed = await proxyJson(new Request("http://frontend/"), "/health", { timeoutMs: 5 });
  assert.equal(timed.status, 504);
  const controller = new AbortController(); controller.abort();
  const cancelled = await proxyJson(new Request("http://frontend/", { signal: controller.signal }), "/health");
  assert.equal(cancelled.status, 499);
});
