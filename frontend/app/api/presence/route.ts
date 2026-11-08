import { proxyJson } from "@/infra/proxy";
export const runtime = "nodejs";
export async function POST(request: Request) {
  return proxyJson(request, "/api/v1/presence", { forwardBody: true, timeoutMs: 15_000 });
}
