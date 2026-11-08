import type { StreamChatInput, RequestStatus } from "../../matrix/types.ts";

export type TurnPhase = RequestStatus | "idle" | "confirming" | "unknown";
export type TurnOutcome = { phase: TurnPhase; reply?: string; persona?: string; error?: string };
type Sender = (input: StreamChatInput) => Promise<{ reply: string; meta: { active_persona?: string } | null }>;
type Canceller = (session: string, request: string) => Promise<{ status: RequestStatus; result?: { reply: string; active_persona: string } | null }>;

/** Owns request identity, cancellation and recovery independently from React/rendering. */
export class TurnLifecycle {
  phase: TurnPhase = "idle";
  private controller: AbortController | null = null;
  private retry: { key: string; id: string } | null = null;
  private listeners = new Set<() => void>();
  private sendRequest: Sender;
  private cancelRequest: Canceller;
  private timeoutMs: number;
  constructor(sendRequest: Sender, cancelRequest: Canceller, timeoutMs = 120_000) {
    this.sendRequest = sendRequest; this.cancelRequest = cancelRequest; this.timeoutMs = timeoutMs;
  }
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  snapshot = () => this.phase;
  get busy() { return this.phase === "generating" || this.phase === "confirming"; }
  private transition(phase: TurnPhase) { this.phase = phase; for (const listener of this.listeners) listener(); }
  stop = () => this.controller?.abort();

  async send(input: StreamChatInput): Promise<TurnOutcome> {
    if (this.busy) throw new Error("已有回合正在处理");
    const key = JSON.stringify([input.sessionId, input.memoryThreadId, input.text, input.model, input.reasoningEffort]);
    const id = this.retry?.key === key ? this.retry.id : crypto.randomUUID();
    this.retry = { key, id };
    const controller = new AbortController();
    this.controller = controller;
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    this.transition("generating");
    try {
      const result = await this.sendRequest({ ...input, requestId: id, signal: controller.signal });
      this.retry = null;
      this.transition("completed");
      return { phase: "completed", reply: result.reply, persona: result.meta?.active_persona };
    } catch (error) {
      this.transition("confirming");
      try {
        const state = await this.cancelRequest(input.sessionId, id);
        if (state.status === "completed" && state.result) {
          this.retry = null;
          this.transition("completed");
          return { phase: "completed", reply: state.result.reply, persona: state.result.active_persona };
        }
        if (state.status === "cancelled") {
          this.retry = null;
          const aborted = error instanceof Error && error.name === "AbortError";
          this.transition("cancelled");
          return { phase: "cancelled", error: aborted ? "此回合已取消，未保存对话。" : error instanceof Error ? error.message : String(error) };
        }
        this.transition("committing");
        return { phase: "committing", error: "此回合已保存到本地，长期记忆尚未确认完成。再次发送相同内容将继续原回合。请选择重新接通查看历史。" };
      } catch {
        this.transition("unknown");
        return { phase: "unknown", error: "连接中断，尚未确认回合状态。再次发送相同内容将查询或继续原回合。" };
      }
    } finally {
      clearTimeout(timer);
      if (this.controller === controller) this.controller = null;
    }
  }
}
