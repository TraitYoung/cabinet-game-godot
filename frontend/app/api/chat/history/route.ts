import { proxyJson } from "@/infra/proxy";
export const runtime = "nodejs";
export async function GET(request: Request) {
  return proxyJson(request, "/api/v1/chat/history", { requireSession: true });
}
