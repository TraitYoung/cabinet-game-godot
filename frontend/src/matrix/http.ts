export class ApiError extends Error {
  status: number;
  code: string;
  constructor(message: string, status: number, code: string) { super(message); this.status = status; this.code = code; }
}

export async function readApiError(response: Response, fallback = "请求失败"): Promise<ApiError> {
  const text = await response.text().catch(() => "");
  let message = fallback;
  let code = `http_${response.status}`;
  try {
    const data = JSON.parse(text) as { code?: string; detail?: unknown };
    code = data.code || code;
    if (typeof data.detail === "string") message = data.detail;
    else if (Array.isArray(data.detail)) message = data.detail.map((item) => item.msg || String(item)).join("; ");
  } catch { if (text) message = text; }
  return new ApiError(message, response.status, code);
}

export async function apiFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const response = await fetch(input, init);
  if (!response.ok) throw await readApiError(response);
  return response;
}
