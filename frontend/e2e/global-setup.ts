import { chromium, FullConfig } from "@playwright/test";
import {
  AUTH_STORAGE,
  TEST_USERS,
  loginAsUser,
  loginAsPartner,
  loginAsTenant,
  TestUser,
} from "./fixtures/auth.fixture";
import fs from "fs";
import path from "path";

/**
 * Global setup for Playwright tests
 * Handles authentication and saves storage state for reuse
 */
async function globalSetup(config: FullConfig) {
  const { baseURL } = config.projects[0].use;

  // Ensure auth directory exists
  const authDir = path.dirname(AUTH_STORAGE.admin);
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
  }

  const browser = await chromium.launch();

  // Setup admin authentication
  console.log("Setting up admin authentication...");
  try {
    const adminContext = await browser.newContext({ baseURL });
    await adminContext.addCookies([
      { name: "playwright_test", value: "1", domain: "localhost", path: "/" },
    ]);
    const adminPage = await adminContext.newPage();

    await loginAsUser(adminPage, TEST_USERS.admin);
    await adminContext.storageState({ path: AUTH_STORAGE.admin });

    console.log("  Admin auth state saved");
    await adminContext.close();
  } catch (error) {
    console.log("  Admin login failed:", (error as Error).message);
    console.log("  Using mock auth state");
    await createMockAuthState(AUTH_STORAGE.admin, TEST_USERS.admin, "admin");
  }

  // Setup partner authentication
  console.log("Setting up partner authentication...");
  try {
    const partnerContext = await browser.newContext({ baseURL });
    await partnerContext.addCookies([
      { name: "playwright_test", value: "1", domain: "localhost", path: "/" },
    ]);
    const partnerPage = await partnerContext.newPage();

    await loginAsPartner(partnerPage, TEST_USERS.partner);
    await partnerContext.storageState({ path: AUTH_STORAGE.partner });

    console.log("  Partner auth state saved");
    await partnerContext.close();
  } catch (error) {
    console.log("  Partner login failed:", (error as Error).message);
    console.log("  Using mock auth state");
    await createMockAuthState(AUTH_STORAGE.partner, TEST_USERS.partner, "partner");
  }

  // Setup tenant authentication
  console.log("Setting up tenant authentication...");
  try {
    const tenantContext = await browser.newContext({ baseURL });
    await tenantContext.addCookies([
      { name: "playwright_test", value: "1", domain: "localhost", path: "/" },
    ]);
    const tenantPage = await tenantContext.newPage();

    await loginAsTenant(tenantPage, TEST_USERS.tenant);
    await tenantContext.storageState({ path: AUTH_STORAGE.tenant });

    console.log("  Tenant auth state saved");
    await tenantContext.close();
  } catch (error) {
    console.log("  Tenant login failed:", (error as Error).message);
    console.log("  Using mock auth state");
    await createMockAuthState(AUTH_STORAGE.tenant, TEST_USERS.tenant, "tenant");
  }

  await browser.close();
}

/**
 * Create mock auth state for CI/testing without real backend
 */
async function createMockAuthState(
  statePath: string,
  user: TestUser,
  role: string
): Promise<void> {
  const baseURL = process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000";
  const mockState = {
    cookies: [
      {
        name: "playwright_test",
        value: "1",
        domain: "localhost",
        path: "/",
        expires: Math.floor(Date.now() / 1000) + 86400,
        httpOnly: false,
        secure: false,
        sameSite: "Lax" as const,
      },
      {
        name: "access_token",
        value: `mock_access_token_${role}_${Date.now()}`,
        domain: "localhost",
        path: "/",
        expires: Math.floor(Date.now() / 1000) + 86400, // 24 hours
        httpOnly: true,
        secure: false,
        sameSite: "Lax" as const,
      },
      {
        name: "session",
        value: JSON.stringify({
          user: {
            id: `${role}-user-id`,
            email: user.email,
            role: role,
          },
        }),
        domain: "localhost",
        path: "/",
        expires: Math.floor(Date.now() / 1000) + 86400,
        httpOnly: false,
        secure: false,
        sameSite: "Lax" as const,
      },
    ],
    origins: [
      {
        origin: baseURL,
        localStorage: [
          {
            name: "user",
            value: JSON.stringify({
              id: `${role}-user-id`,
              email: user.email,
              role: role,
            }),
          },
        ],
      },
    ],
  };

  fs.writeFileSync(statePath, JSON.stringify(mockState, null, 2));
}

export default globalSetup;
