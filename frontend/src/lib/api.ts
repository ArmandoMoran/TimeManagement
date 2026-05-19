import { tokenStore } from "./tokenStore";

const API_BASE = "/api/v1";

export type ApiErrorBody = {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
};

export class ApiError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly details?: Record<string, unknown>;

  public constructor(status: number, body: ApiErrorBody) {
    super(body.error.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.error.code;
    if (body.error.details !== undefined) {
      this.details = body.error.details;
    }
  }
}

type Method = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

type RequestOptions = {
  method?: Method;
  json?: unknown;
  query?: Record<string, string | number | boolean | undefined>;
  signal?: AbortSignal;
  /** Forces use of the refresh token instead of the access token. */
  useRefreshToken?: boolean;
  /** Skips the automatic refresh-on-401 retry (prevents recursion). */
  skipAutoRefresh?: boolean;
};

let refreshInFlight: Promise<void> | null = null;

async function attemptRefresh(): Promise<void> {
  const refresh = tokenStore.getRefreshToken();
  if (!refresh) throw new Error("no refresh token");

  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const response = await fetch(`${API_BASE}/auth/refresh`, {
          method: "POST",
          headers: { Authorization: `Bearer ${refresh}` },
        });
        if (!response.ok) {
          tokenStore.clear();
          throw new Error("refresh failed");
        }
        const body = (await response.json()) as {
          access_token: string;
          refresh_token: string;
        };
        tokenStore.setTokens(body.access_token, body.refresh_token);
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  await refreshInFlight;
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  if (!query) return `${API_BASE}${path}`;
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value !== undefined) params.set(key, String(value));
  }
  const qs = params.toString();
  return qs ? `${API_BASE}${path}?${qs}` : `${API_BASE}${path}`;
}

export async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  if (options.json !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  const token = options.useRefreshToken
    ? tokenStore.getRefreshToken()
    : tokenStore.getAccessToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const init: RequestInit = {
    method: options.method ?? "GET",
    headers,
  };
  if (options.json !== undefined) init.body = JSON.stringify(options.json);
  if (options.signal) init.signal = options.signal;

  const response = await fetch(buildUrl(path, options.query), init);

  if (
    response.status === 401 &&
    !options.skipAutoRefresh &&
    !options.useRefreshToken &&
    tokenStore.getRefreshToken()
  ) {
    try {
      await attemptRefresh();
    } catch {
      throw new ApiError(401, {
        error: { code: "session_expired", message: "session expired" },
      });
    }
    return request<T>(path, { ...options, skipAutoRefresh: true });
  }

  if (!response.ok) {
    const body = (await response
      .json()
      .catch(() => ({
        error: { code: "unknown", message: response.statusText },
      }))) as ApiErrorBody;
    throw new ApiError(response.status, body);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string, query?: RequestOptions["query"]) => {
    const opts: RequestOptions = { method: "GET" };
    if (query !== undefined) opts.query = query;
    return request<T>(path, opts);
  },
  post: <T>(path: string, json?: unknown) => {
    const opts: RequestOptions = { method: "POST" };
    if (json !== undefined) opts.json = json;
    return request<T>(path, opts);
  },
  patch: <T>(path: string, json?: unknown) => {
    const opts: RequestOptions = { method: "PATCH" };
    if (json !== undefined) opts.json = json;
    return request<T>(path, opts);
  },
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
