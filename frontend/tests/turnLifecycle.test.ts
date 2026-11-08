import test from "node:test";
import assert from "node:assert/strict";
import { TurnLifecycle } from "../src/modules/solo-chat/turnLifecycle.ts";
import type { StreamChatInput } from "../src/matrix/types.ts";

const input = { text: "hello", sessionId: "session", memoryThreadId: "user" };
test("successful turn clears retry identity and notifies subscribers", async () => {
  const ids: (string | undefined)[] = [];
  const phases: string[] = [];
  const turn = new TurnLifecycle(async (request) => { ids.push(request.requestId); return { reply: "hello", meta: null }; }, async () => ({ status: "cancelled" }));
  turn.subscribe(() => phases.push(turn.phase));
  assert.equal((await turn.send(input)).reply, "hello");
  await turn.send(input); assert.notEqual(ids[0], ids[1]);
  assert.deepEqual(phases.slice(0, 2), ["generating", "completed"]);
});
for (const status of ["cancelled", "committing", "completed", "unknown"] as const) {
  test(`timeout/unmount recovery handles ${status}`, async () => {
    const ids: (string | undefined)[] = [];
    let fail = true;
    const sender = async (request: StreamChatInput) => {
      ids.push(request.requestId);
      if (fail) throw new DOMException("Aborted", "AbortError");
      return { reply: "retried", meta: null };
    };
    const turn = new TurnLifecycle(sender, async () => {
      if (status === "unknown") throw new Error("offline");
      return { status, result: status === "completed" ? { reply: "saved", active_persona: "bina" } : null };
    });
    const outcome = await turn.send(input);
    assert.equal(outcome.phase, status);
    assert.equal(turn.busy, false);
    if (status === "completed") assert.equal(outcome.reply, "saved");
    fail = false;
    await turn.send(input);
    if (status === "committing" || status === "unknown") assert.equal(ids[0], ids[1]);
    else assert.notEqual(ids[0], ids[1]);
  });
}
test("stop and deadline abort the active request; concurrent sends are rejected", async () => {
  const sender = async (request: StreamChatInput): Promise<never> => new Promise((_, reject) => {
    request.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
  });
  const turn = new TurnLifecycle(sender, async () => ({ status: "cancelled" }), 20);
  const pending = turn.send(input);
  await assert.rejects(() => turn.send(input), /正在处理/);
  turn.stop(); assert.equal((await pending).phase, "cancelled");
  assert.equal((await turn.send(input)).phase, "cancelled");
});
