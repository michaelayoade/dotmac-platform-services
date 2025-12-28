/**
 * API Client
 *
 * Centralized HTTP client for backend API communication
 * Handles authentication, error handling, correlation IDs, and response parsing
 */

import type { PaginatedResponse } from "@/types/api";
import { ApiClientError, type BackendError } from "./errors";

export type { PaginatedResponse };
export { ApiClientError } from "./errors";
export type { BackendError } from "./errors";

const API_BASE_URL =
  (typeof window === "undefined"
    ? process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL
    : process.env.NEXT_PUBLIC_API_URL) || "http://localhost:8000";


interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
  requiresAuth?: boolean;
  timeout?: number;
  retries?: number;
  json?: unknown;
  responseType?: "json" | "blob";
  transformRequest?: boolean;
  transformParams?: boolean;
  transformResponse?: boolean;
}

// Generate a correlation ID for request tracing
function generateCorrelationId(): string {
  return `fe_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Object.prototype.toString.call(value) === "[object Object]";
}

function toSnakeCaseKey(key: string): string {
  return key.replace(/([A-Z])/g, "_$1").replace(/-/g, "_").toLowerCase();
}

function toCamelCaseKey(key: string): string {
  return key.replace(/[_-]([a-z0-9])/g, (_, char: string) => char.toUpperCase());
}

function convertKeysDeep<T>(value: T, convertKey: (key: string) => string): T {
  if (Array.isArray(value)) {
    return value.map((item) => convertKeysDeep(item, convertKey)) as T;
  }

  if (isPlainObject(value)) {
    const result: Record<string, unknown> = {};
    for (const [key, val] of Object.entries(value)) {
      result[convertKey(key)] = convertKeysDeep(val, convertKey);
    }
    return result as T;
  }

  return value;
}

function coerceOptionalBoolean(value: unknown): boolean | undefined {
  if (typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    return value !== 0;
  }
  return undefined;
}

export function normalizePaginatedResponse<T>(
  payload: unknown
): PaginatedResponse<T> {
  if (Array.isArray(payload)) {
    const items = payload as T[];
    const total = items.length;

    return {
      items,
      total,
      page: 1,
      pageSize: total,
      totalPages: total ? 1 : 0,
      hasNext: false,
      hasPrev: false,
    };
  }

  if (!payload || typeof payload !== "object") {
    return {
      items: [],
      total: 0,
      page: 1,
      pageSize: 0,
      totalPages: 0,
    };
  }

  const data = payload as Record<string, unknown>;
  const meta: Record<string, unknown> = isPlainObject(data.meta) ? data.meta : {};

  const itemsValue =
    data.items ??
    data.users ??
    data.customers ??
    data.tenants ??
    data.contacts ??
    data.partners ??
    data.templates ??
    data.jobs ??
    data.logs ??
    data.notifications ??
    data.activities ??
    data.workflows ??
    data.executions ??
    data.invoices ??
    data.subscriptions ??
    data.payments ??
    data.deliveries ??
    data.tickets ??
    data.instances ??
    data.deployments ??
    data.licenses ??
    data.data ??
    data.results ??
    data.records ??
    data.entries ??
    meta.items ??
    meta.data ??
    meta.results ??
    [];
  const items = Array.isArray(itemsValue) ? (itemsValue as T[]) : [];

  const totalValue =
    data.total ??
    data.totalCount ??
    data.total_count ??
    data.count ??
    meta.total ??
    meta.totalCount ??
    meta.total_count ??
    meta.count ??
    items.length;
  const total = Number.isFinite(Number(totalValue)) ? Number(totalValue) : items.length;

  const pageSizeValue =
    data.pageSize ??
    data.perPage ??
    data.page_size ??
    data.per_page ??
    data.limit ??
    meta.pageSize ??
    meta.perPage ??
    meta.page_size ??
    meta.per_page ??
    meta.limit ??
    0;
  let pageSize = Number(pageSizeValue);
  if (!Number.isFinite(pageSize) || pageSize < 0) {
    pageSize = 0;
  }
  if (pageSize === 0 && items.length > 0) {
    pageSize = items.length;
  }

  let page = Number(data.page ?? meta.page ?? 1);
  if (!Number.isFinite(page) || page < 1) {
    page = 1;
  }
  const offsetValue = data.offset ?? meta.offset;
  if ((data.page === undefined && meta.page === undefined) && pageSize > 0 && offsetValue !== undefined) {
    const offset = Number(offsetValue);
    if (Number.isFinite(offset) && offset >= 0) {
      page = Math.floor(offset / pageSize) + 1;
    }
  }

  let totalPages = Number(
    data.totalPages ??
      data.total_pages ??
      data.pages ??
      meta.totalPages ??
      meta.total_pages ??
      (pageSize ? Math.ceil(total / pageSize) : 0)
  );
  if (!Number.isFinite(totalPages) || totalPages < 0) {
    totalPages = pageSize ? Math.ceil(total / pageSize) : 0;
  }
  const hasNextValue =
    data.hasNext ??
    data.has_next ??
    data.hasMore ??
    data.has_more ??
    meta.hasNext ??
    meta.has_next ??
    meta.hasMore ??
    meta.has_more ??
    (totalPages ? page < totalPages : undefined);
  const hasPrevValue =
    data.hasPrev ??
    data.has_prev ??
    data.hasPrevious ??
    data.has_previous ??
    meta.hasPrev ??
    meta.has_prev ??
    meta.hasPrevious ??
    meta.has_previous ??
    (page > 1 ? true : undefined);
  const hasNext = coerceOptionalBoolean(hasNextValue);
  const hasPrev = coerceOptionalBoolean(hasPrevValue);

  return {
    items,
    total,
    page,
    pageSize,
    totalPages,
    hasNext,
    hasPrev,
  };
}

async function getAuthHeaders(): Promise<Record<string, string>> {
  try {
    if (typeof window === "undefined") {
      const { getServerSession } = await import("next-auth");
      const { authOptions } = await import("@/lib/auth/config");
      const session = await getServerSession(authOptions);
      const token = session?.accessToken;
      const tenantId = session?.user?.tenantId ?? undefined;
      return token
        ? {
            Authorization: `Bearer ${token}`,
            ...(tenantId ? { "X-Tenant-ID": tenantId } : {}),
          }
        : {};
    }

    const { getSession } = await import("next-auth/react");
    const session = await getSession();
    const token = session?.accessToken;
    const tenantId = session?.user?.tenantId ?? undefined;
    return token
      ? {
          Authorization: `Bearer ${token}`,
          ...(tenantId ? { "X-Tenant-ID": tenantId } : {}),
        }
      : {};
  } catch {
    return {};
  }
}

function isUnsafeMethod(method: string): boolean {
  return !["GET", "HEAD", "OPTIONS", "TRACE"].includes(method);
}

function getBrowserCookie(name: string): string | null {
  if (typeof document === "undefined") {
    return null;
  }
  const cookieString = document.cookie || "";
  const parts = cookieString.split("; ").map((part) => part.split("="));
  for (const [key, value] of parts) {
    if (key === name) {
      return decodeURIComponent(value ?? "");
    }
  }
  return null;
}

async function getCookieHeaders(method: string): Promise<Record<string, string>> {
  const headers: Record<string, string> = {};

  if (typeof window === "undefined") {
    try {
      const { cookies } = await import("next/headers");
      const cookieStore = cookies();
      const allCookies = cookieStore.getAll();
      if (allCookies.length > 0) {
        headers["Cookie"] = allCookies
          .map((cookie) => `${cookie.name}=${cookie.value}`)
          .join("; ");
      }
      if (isUnsafeMethod(method)) {
        const csrfToken = cookieStore.get("csrf_token")?.value;
        if (csrfToken) {
          headers["X-CSRF-Token"] = csrfToken;
        }
      }
    } catch {
      // Server cookies not available, proceed without auth headers
    }
    return headers;
  }

  if (isUnsafeMethod(method)) {
    const csrfToken = getBrowserCookie("csrf_token");
    if (csrfToken) {
      headers["X-CSRF-Token"] = csrfToken;
    }
  }

  return headers;
}

async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const {
    params,
    requiresAuth = true,
    timeout = 30000,
    retries = 0,
    json,
    responseType = "json",
    transformRequest = true,
    transformParams = true,
    transformResponse = true,
    ...fetchOptions
  } = options;
  const method = (fetchOptions.method ?? "GET").toUpperCase();
  const isTestMode =
    process.env.PLAYWRIGHT_TEST_MODE === "true" ||
    process.env.NEXT_PUBLIC_TEST_MODE === "true";

  if (isTestMode && method === "GET") {
    const { getTestMockResponse } = await import("./test-mocks");
    const mocked = getTestMockResponse(endpoint);
    if (mocked !== undefined) {
      return mocked as T;
    }
  }

  // Build URL with query params
  const url = new URL(`${API_BASE_URL}${endpoint}`);
  if (params) {
    const normalizedParams = transformParams
      ? (convertKeysDeep(params, toSnakeCaseKey) as Record<string, string | number | boolean | undefined>)
      : params;

    Object.entries(normalizedParams).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    });
  }

  // Generate correlation ID for tracing
  const correlationId = generateCorrelationId();

  // Build headers
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
    "X-Correlation-ID": correlationId,
    "X-Request-ID": correlationId,
    ...(fetchOptions.headers as Record<string, string>),
  };

  if (requiresAuth) {
    const authHeaders = await getAuthHeaders();
    const cookieHeaders = await getCookieHeaders(method);
    Object.assign(headers, authHeaders);
    if (!headers["Cookie"] && cookieHeaders["Cookie"]) {
      headers["Cookie"] = cookieHeaders["Cookie"];
    }
    if (cookieHeaders["X-CSRF-Token"]) {
      headers["X-CSRF-Token"] = cookieHeaders["X-CSRF-Token"];
    }
  }

  if (json !== undefined) {
    const payload = transformRequest ? convertKeysDeep(json, toSnakeCaseKey) : json;
    fetchOptions.body = JSON.stringify(payload);
  }

  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  let lastError: Error | null = null;
  let attempts = 0;

  while (attempts <= retries) {
    try {
      const response = await fetch(url.toString(), {
        ...fetchOptions,
        headers,
        credentials: fetchOptions.credentials ?? "include",
        signal: controller.signal,
        next: { revalidate: 0 }, // Disable caching for dynamic data
      });

      clearTimeout(timeoutId);

      // Handle errors
      if (!response.ok) {
        let errorData: BackendError;
        try {
          errorData = await response.json();
        } catch {
          errorData = {
            error_code: "UNKNOWN_ERROR",
            message: `Request failed with status ${response.status}`,
            status: response.status,
          };
        }

        const error = ApiClientError.fromBackendError(errorData);

        // Don't retry auth errors or validation errors
        if (error.isAuthError() || error.isValidationError()) {
          throw error;
        }

        // For retryable errors, continue to next attempt
        if (error.retryable && attempts < retries) {
          lastError = error;
          attempts++;
          await new Promise((resolve) =>
            setTimeout(resolve, Math.pow(2, attempts) * 1000)
          );
          continue;
        }

        throw error;
      }

      // Parse response
      if (response.status === 204) {
        return undefined as T;
      }

      if (responseType === "blob") {
        return (await response.blob()) as T;
      }

      const data = await response.json();
      return (transformResponse
        ? convertKeysDeep(data, toCamelCaseKey)
        : data) as T;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof ApiClientError) {
        throw error;
      }

      // Handle timeout
      if (error instanceof Error && error.name === "AbortError") {
        throw new ApiClientError(
          "Request timed out",
          408,
          "TIMEOUT_ERROR",
          "The request took too long to complete. Please try again.",
          undefined,
          undefined,
          correlationId,
          true
        );
      }

      // Handle network errors
      if (error instanceof TypeError && error.message.includes("fetch")) {
        throw new ApiClientError(
          "Network error",
          0,
          "NETWORK_ERROR",
          "Unable to connect to the server. Please check your connection.",
          undefined,
          undefined,
          correlationId,
          true
        );
      }

      throw error;
    }
  }

  // If we've exhausted retries, throw the last error
  if (lastError) {
    throw lastError;
  }

  // This shouldn't happen, but just in case
  throw new ApiClientError(
    "Request failed after retries",
    500,
    "RETRY_EXHAUSTED",
    "The request failed after multiple attempts.",
    undefined,
    undefined,
    correlationId
  );
}

// Convenience methods
export const api = {
  get: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: "GET" }),

  post: <T>(endpoint: string, data?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: "POST",
      json: data,
    }),

  put: <T>(endpoint: string, data?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: "PUT",
      json: data,
    }),

  patch: <T>(endpoint: string, data?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: "PATCH",
      json: data,
    }),

  delete: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: "DELETE" }),

  getBlob: (endpoint: string, options?: RequestOptions) =>
    request<Blob>(endpoint, {
      ...options,
      method: "GET",
      responseType: "blob",
      transformResponse: false,
    }),
};

// Export base URL for external use
export { API_BASE_URL };
