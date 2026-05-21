import type {
  ChatRequestBody,
  ChatResponseBody,
  HealthResponseBody,
  TaxAnalysisResponseBody,
  TaxRulesResponseBody,
  TaxScenarioRequestBody,
} from "./apiTypes";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(message: string, status: number, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

const DEFAULT_BASE_URL = "/api";

function baseUrl(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL;
  if (typeof fromEnv === "string" && fromEnv.length > 0) {
    return fromEnv.replace(/\/+$/, "");
  }
  return DEFAULT_BASE_URL;
}

async function request<T>(
  path: string,
  init: RequestInit & { signal?: AbortSignal } = {},
): Promise<T> {
  const url = `${baseUrl()}${path}`;
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(url, { ...init, headers });
  } catch (err) {
    throw new ApiError(
      err instanceof Error ? err.message : "Network request failed",
      0,
    );
  }

  const text = await response.text();
  let parsed: unknown = undefined;
  if (text.length > 0) {
    try {
      parsed = JSON.parse(text);
    } catch {
      parsed = text;
    }
  }

  if (!response.ok) {
    throw new ApiError(
      `Request to ${path} failed (${response.status})`,
      response.status,
      parsed,
    );
  }

  return parsed as T;
}

export function getHealth(signal?: AbortSignal): Promise<HealthResponseBody> {
  return request<HealthResponseBody>("/health", { method: "GET", signal });
}

export function postChat(
  body: ChatRequestBody,
  signal?: AbortSignal,
): Promise<ChatResponseBody> {
  return request<ChatResponseBody>("/chat", {
    method: "POST",
    body: JSON.stringify(body),
    signal,
  });
}

export function postAnalyze(
  body: TaxScenarioRequestBody,
  signal?: AbortSignal,
): Promise<TaxAnalysisResponseBody> {
  return request<TaxAnalysisResponseBody>("/tax/analyze", {
    method: "POST",
    body: JSON.stringify(body),
    signal,
  });
}

export function getTaxRules(
  taxYear: number,
  stateCode?: string | null,
  signal?: AbortSignal,
): Promise<TaxRulesResponseBody> {
  const params = new URLSearchParams({ tax_year: String(taxYear) });
  if (stateCode) params.set("state_code", stateCode.toUpperCase());
  return request<TaxRulesResponseBody>(`/tax/rules?${params.toString()}`, {
    method: "GET",
    signal,
  });
}
