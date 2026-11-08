import { proxyJson } from "@/infra/proxy";
export const runtime = "nodejs";
export async function GET(request: Request) {
  return proxyJson(request, "/api/v1/health", { timeoutMs: 5_000 });
}
