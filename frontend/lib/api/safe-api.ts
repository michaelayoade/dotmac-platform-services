import { ApiClientError } from "./client";

export function isNetworkError(error: unknown): error is ApiClientError {
  return error instanceof ApiClientError && error.code === "NETWORK_ERROR";
}

export async function safeApi<T>(fn: () => Promise<T>, fallback: T): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    if (isNetworkError(error)) {
      return fallback;
    }
    throw error;
  }
}
