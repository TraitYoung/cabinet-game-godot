import { proxyJson } from "@/infra/proxy";
export const runtime = "nodejs";
export async function POST(request: Request) {
  return proxyJson(request, "/api/v1/chat/export", { requireSession: true, timeoutMs: 60_000 });
}
