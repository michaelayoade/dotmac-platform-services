import { api, ApiClientError } from "@/lib/api/client";
import type { PlatformUser } from "@/types/auth";

export async function getCurrentUserFromRequest(): Promise<PlatformUser | null> {
  try {
    return await api.get<PlatformUser>("/api/v1/auth/me");
  } catch (error) {
    if (error instanceof ApiClientError) {
      if (error.isAuthError() || error.status === 0) {
        return null;
      }
    }
    throw error;
  }
}
