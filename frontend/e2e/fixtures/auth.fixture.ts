import { test as base, Page } from "@playwright/test";
import path from "path";

// Storage paths for auth states
const STORAGE_STATE_DIR = path.join(__dirname, "../../playwright/.auth");

export const AUTH_STORAGE = {
  admin: path.join(STORAGE_STATE_DIR, "admin.json"),
  partner: path.join(STORAGE_STATE_DIR, "partner.json"),
  tenant: path.join(STORAGE_STATE_DIR, "tenant.json"),
} as const;

// User credentials interface
export interface TestUser {
  email: string;
  password: string;
  storageState: string;
}

// Test users configuration
export const TEST_USERS: Record<string, TestUser> = {
  admin: {
    email: process.env.TEST_ADMIN_EMAIL || "admin@test.local",
    password: process.env.TEST_ADMIN_PASSWORD || "TestPassword123!",
    storageState: AUTH_STORAGE.admin,
  },
  partner: {
    email: process.env.TEST_PARTNER_EMAIL || "partner@test.local",
    password: process.env.TEST_PARTNER_PASSWORD || "TestPassword123!",
    storageState: AUTH_STORAGE.partner,
  },
  tenant: {
    email: process.env.TEST_TENANT_EMAIL || "tenant@test.local",
    password: process.env.TEST_TENANT_PASSWORD || "TestPassword123!",
    storageState: AUTH_STORAGE.tenant,
  },
};

/**
 * Login helper function for authentication
 */
export async function loginAsUser(page: Page, user: TestUser): Promise<void> {
  await page.goto("/login");

  // Wait for login form to be ready
  await page.waitForSelector('input[type="email"], input#email, input[name="email"]');

  // Fill in credentials
  await page.locator('input[type="email"], input#email, input[name="email"]').fill(user.email);
  await page.locator('input[type="password"], input#password, input[name="password"]').fill(user.password);

  // Submit form
  await page.locator('button[type="submit"]').click();

  // Wait for redirect after successful login
  await page.waitForURL("/**", { waitUntil: "networkidle" });
}

/**
 * Login to partner portal
 */
export async function loginAsPartner(page: Page, user: TestUser): Promise<void> {
  await page.goto("/partner/login");

  // Wait for login form to be ready
  await page.waitForSelector('input[type="email"], input#email, input[name="email"]');

  // Fill in credentials
  await page.locator('input[type="email"], input#email, input[name="email"]').fill(user.email);
  await page.locator('input[type="password"], input#password, input[name="password"]').fill(user.password);

  // Submit form
  await page.locator('button[type="submit"]').click();

  // Wait for redirect after successful login
  await page.waitForURL("**/partner/**", { waitUntil: "networkidle" });
}

/**
 * Login to tenant portal
 */
export async function loginAsTenant(page: Page, user: TestUser): Promise<void> {
  await page.goto("/portal/login");

  // Wait for login form to be ready
  await page.waitForSelector('input[type="email"], input#email, input[name="email"]');

  // Fill in credentials
  await page.locator('input[type="email"], input#email, input[name="email"]').fill(user.email);
  await page.locator('input[type="password"], input#password, input[name="password"]').fill(user.password);

  // Submit form
  await page.locator('button[type="submit"]').click();

  // Wait for redirect after successful login
  await page.waitForURL("**/portal/**", { waitUntil: "networkidle" });
}

// Extended test fixture types
type AuthFixture = {
  adminPage: Page;
  partnerPage: Page;
  tenantPage: Page;
};

/**
 * Extended test fixture with pre-authenticated pages
 */
export const test = base.extend<AuthFixture>({
  // Admin authenticated page
  adminPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: AUTH_STORAGE.admin,
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },

  // Partner authenticated page
  partnerPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: AUTH_STORAGE.partner,
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },

  // Tenant authenticated page
  tenantPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: AUTH_STORAGE.tenant,
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },
});

export { expect } from "@playwright/test";
