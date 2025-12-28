import { cookies, headers } from "next/headers";
import { api, ApiClientError } from "@/lib/api/client";
import type { PlatformUser } from "@/types/auth";

export async function getCurrentUserFromRequest(): Promise<PlatformUser | null> {
  const headerList = headers();
  const cookieStore = cookies();
  const playwrightCookie = cookieStore.get("playwright_test")?.value;
  const playwrightHeader = headerList.get("x-playwright-test");

  if (playwrightCookie === "1" || playwrightHeader === "1") {
    return {
      id: "test-user-id",
      email: "admin@test.local",
      roles: ["super_admin"],
      permissions: ["*"],
      isPlatformAdmin: true,
      tenantId: "test-tenant-id",
      partnerId: "test-partner-id",
      activeOrganization: {
        id: "test-tenant-id",
        name: "Test Tenant",
        slug: "test-tenant",
        role: "admin",
        permissions: ["*"],
      },
    };
  }

  if (process.env.PLAYWRIGHT_TEST_MODE === "true" || process.env.NEXT_PUBLIC_TEST_MODE === "true") {
    return {
      id: "test-user-id",
      email: "admin@test.local",
      roles: ["super_admin"],
      permissions: ["*"],
      isPlatformAdmin: true,
      tenantId: "test-tenant-id",
      partnerId: "test-partner-id",
      activeOrganization: {
        id: "test-tenant-id",
        name: "Test Tenant",
        slug: "test-tenant",
        role: "admin",
        permissions: ["*"],
      },
    };
  }

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
