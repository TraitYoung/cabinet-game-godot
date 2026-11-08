/** Thin JSON proxy shared by Route Handlers. Streaming /api/v1 uses Next rewrites. */
import { getBackendBaseUrl } from "./backend.ts";

export async function proxyJson(request: Request, path: string, options: {
  timeoutMs?: number; requireSession?: boolean; forwardBody?: boolean;
} = {}): Promise<Response> {
  const session = request.headers.get("x-session-id");
  if (options.requireSession && !session) {
    return Response.json({ code: "invalid_request", detail: "缺少会话 ID" }, { status: 400 });
  }
  const headers = new Headers({ "Content-Type": "application/json" });
  for (const name of ["x-session-id", "x-memory-thread", "x-trace-id"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  const signal = AbortSignal.any([request.signal, AbortSignal.timeout(options.timeoutMs ?? 8_000)]);
  try {
    const body = options.forwardBody ? await request.text() : undefined;
    const response = await fetch(`${getBackendBaseUrl()}${path}${new URL(request.url).search}`, {
      method: request.method, headers, body, signal, cache: "no-store",
    });
    const raw = await response.text();
    let data: unknown;
    try { data = JSON.parse(raw); }
    catch {
      return Response.json({ code: "invalid_response", detail: "后端返回了无效的 JSON" }, { status: 502 });
    }
    return Response.json(data, { status: response.status });
  } catch {
    const status = request.signal.aborted ? 499 : signal.aborted ? 504 : 503;
    return Response.json({ code: status === 499 ? "cancelled" : status === 504 ? "backend_timeout" : "backend_unavailable",
      detail: status === 499 ? "请求已取消" : status === 504 ? "后端响应超时" : "无法连接后端，请检查服务状态" }, { status });
  }
}
