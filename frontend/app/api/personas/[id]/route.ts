import { proxyJson } from "@/infra/proxy";
export const runtime = "nodejs";
export async function GET(request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  return proxyJson(request, `/api/v1/personas/${encodeURIComponent(id)}`);
}
