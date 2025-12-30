import { test, expect } from "../../fixtures";
import { DashboardPage, UsersPage, TenantsPage, SettingsPage } from "../../pages/dashboard";
import { expectLoadingComplete, expectNoErrors } from "../../utils/assertions";
import { STATIC_DASHBOARD_ROUTES, ROUTE_COUNTS } from "../../utils/test-data";
import { setupApiMocks } from "../../utils/api-mocks";

test.describe("Dashboard Smoke Tests", () => {
  // Use admin auth for all dashboard tests
  test.use({ storageState: "playwright/.auth/admin.json" });

  test.describe("Main Dashboard", () => {
    test("should load main dashboard", async ({ page }) => {
      await setupApiMocks(page);
      const dashboardPage = new DashboardPage(page);
      await dashboardPage.navigate();
      await expectLoadingComplete(page);

      // Check main elements are visible
      await expect(dashboardPage.getHeader()).toBeVisible();
      await expect(dashboardPage.getMainContent()).toBeVisible();

      await expectNoErrors(page);
    });

  test("should display sidebar navigation", async ({ page }) => {
    await setupApiMocks(page);
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.navigate();
    await expectLoadingComplete(page);

    // Sidebar should have key navigation items
    const sidebar = page.locator('nav[aria-label="Main navigation"], aside nav').first();
    await expect(sidebar).toBeVisible();
    await expect(sidebar.getByRole("link", { name: /billing/i }).first()).toBeVisible();
  });

    test("should have working header with user menu", async ({ page }) => {
      await setupApiMocks(page);
      const dashboardPage = new DashboardPage(page);
      await dashboardPage.navigate();

      // Header should be visible
      await expect(dashboardPage.getHeader()).toBeVisible();

      // User menu should be accessible
      const userButton = page.locator('button[aria-label*="user"], button:has-text("account")').first();
      if (await userButton.isVisible()) {
        await userButton.click();
        await expect(page.locator('[role="menu"]')).toBeVisible();
      }
    });
  });

  test.describe("Users Page", () => {
    test("should load users page", async ({ page }) => {
      await setupApiMocks(page);
      const usersPage = new UsersPage(page);
      await usersPage.navigate();
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/users/);
      await expect(page.getByRole("heading", { name: /users/i })).toBeVisible();
    });

    test("should display users table or list", async ({ page }) => {
      await setupApiMocks(page);
      const usersPage = new UsersPage(page);
      await usersPage.navigate();
      await expectLoadingComplete(page);

      // Should have a table or list of users
      await expect(usersPage.usersTable.or(page.locator('[data-testid="users-list"]'))).toBeVisible();
    });

    test("should have create user action", async ({ page }) => {
      await setupApiMocks(page);
      const usersPage = new UsersPage(page);
      await usersPage.navigate();

      await expect(usersPage.createButton).toBeVisible();
    });
  });

  test.describe("Tenants Page", () => {
    test("should load tenants page", async ({ page }) => {
      await setupApiMocks(page);
      const tenantsPage = new TenantsPage(page);
      await tenantsPage.navigate();
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/tenants/);
      await expect(page.getByRole("heading", { name: /tenants/i })).toBeVisible();
    });

    test("should display tenants table or list", async ({ page }) => {
      await setupApiMocks(page);
      const tenantsPage = new TenantsPage(page);
      await tenantsPage.navigate();
      await expectLoadingComplete(page);

      await expect(
        tenantsPage.tenantsTable
          .or(page.locator('[data-testid="tenants-list"]'))
          .or(page.getByRole("link", { name: /grid view/i }))
      ).toBeVisible();
    });

    test("should have create tenant action", async ({ page }) => {
      await setupApiMocks(page);
      const tenantsPage = new TenantsPage(page);
      await tenantsPage.navigate();

      await expect(tenantsPage.createButton).toBeVisible();
    });
  });

  test.describe("Settings Page", () => {
    test("should load settings page", async ({ page }) => {
      await setupApiMocks(page);
      const settingsPage = new SettingsPage(page);
      await settingsPage.navigate();
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/settings/);
    });

    test("should have settings sections or navigation", async ({ page }) => {
      await setupApiMocks(page);
      const settingsPage = new SettingsPage(page);
      await settingsPage.navigate();
      await expectLoadingComplete(page);

      // Should have some settings sections or tabs
      const settingsNav = page.locator('[data-testid="settings-nav"], nav, .tabs');
      await expect(settingsNav.first()).toBeVisible();
    });
  });

  test.describe("Sidebar Navigation", () => {
  test("sidebar navigation works for billing", async ({ page }) => {
    await setupApiMocks(page);
    await page.goto("/");
    await expectLoadingComplete(page);

    const sidebar = page.locator('nav[aria-label="Main navigation"], aside nav').first();
    await expect(sidebar).toBeVisible();
    await sidebar.getByRole("link", { name: /billing/i }).first().click();
    await expectLoadingComplete(page);

    await expect(page).toHaveURL(/billing/);
  });

  test("sidebar navigation works for users", async ({ page }) => {
    await setupApiMocks(page);
    await page.goto("/");
    await expectLoadingComplete(page);

    const sidebar = page.locator('nav[aria-label="Main navigation"], aside nav').first();
    await expect(sidebar).toBeVisible();
    await sidebar.getByRole("link", { name: /users/i }).first().click();
    await expectLoadingComplete(page);

    await expect(page).toHaveURL(/users/);
  });

  test("sidebar navigation works for tenants", async ({ page }) => {
    await setupApiMocks(page);
    await page.goto("/");
    await expectLoadingComplete(page);

    const sidebar = page.locator('nav[aria-label="Main navigation"], aside nav').first();
    await expect(sidebar).toBeVisible();
    await sidebar.getByRole("link", { name: /tenants/i }).first().click();
    await expectLoadingComplete(page);

    await expect(page).toHaveURL(/tenants/);
  });
  });
});

test.describe("Dashboard Pages Smoke Tests", () => {
  test.use({ storageState: "playwright/.auth/admin.json" });

  // Test all static dashboard pages load without errors
  // Total: ${ROUTE_COUNTS.dashboard} static dashboard routes
  for (const route of STATIC_DASHBOARD_ROUTES) {
    test(`should load ${route.name} (${route.path})`, async ({ page }) => {
      await setupApiMocks(page);
      await page.goto(route.path);

      // Wait for page to load
      await page.waitForLoadState("domcontentloaded");
      await expectLoadingComplete(page);

      // Check that main content area exists
      const mainContent = page.locator("main, #main-content, [role='main']");
      await expect(mainContent.first()).toBeVisible();

      // Should not have any critical errors displayed
      const criticalError = page.locator('[data-testid="critical-error"], .error-boundary');
      await expect(criticalError).not.toBeVisible();
    });
  }
});
