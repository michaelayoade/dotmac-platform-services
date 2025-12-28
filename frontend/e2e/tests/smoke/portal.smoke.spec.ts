import { test, expect } from "../../fixtures";
import {
  PortalLoginPage,
  PortalDashboardPage,
  PortalBillingPage,
  PortalSettingsPage,
  PortalTeamPage,
  PortalUsagePage,
} from "../../pages/portal";
import { expectLoadingComplete, expectNoErrors } from "../../utils/assertions";
import { STATIC_PORTAL_ROUTES } from "../../utils/test-data";
import { setupApiMocks } from "../../utils/api-mocks";

test.describe("Tenant Portal Smoke Tests", () => {
  test.describe("Portal Login", () => {
    test("should display portal login page", async ({ page }) => {
      const portalLoginPage = new PortalLoginPage(page);
      await portalLoginPage.navigate();

      await expect(portalLoginPage.emailInput).toBeVisible();
      await expect(portalLoginPage.passwordInput).toBeVisible();
      await expect(portalLoginPage.submitButton).toBeVisible();
    });

    test("should have forgot password link", async ({ page }) => {
      const portalLoginPage = new PortalLoginPage(page);
      await portalLoginPage.navigate();

      await expect(portalLoginPage.forgotPasswordLink).toBeVisible();
    });
  });
});

test.describe("Tenant Portal Authenticated", () => {
  test.use({ storageState: "playwright/.auth/tenant.json" });

  test.describe("Portal Dashboard", () => {
    test("should load portal dashboard", async ({ page }) => {
      await setupApiMocks(page);
      const dashboardPage = new PortalDashboardPage(page);
      await dashboardPage.navigate();
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/portal/);
      await expectNoErrors(page);
    });

    test("should display portal navigation", async ({ page }) => {
      await setupApiMocks(page);
      const dashboardPage = new PortalDashboardPage(page);
      await dashboardPage.navigate();
      await expectLoadingComplete(page);

      // Should have portal navigation
      const sidebar = page.locator("aside").first();
      await expect(sidebar.getByRole("link", { name: /billing/i }).first()).toBeVisible();
    });

    test("should have help link", async ({ page }) => {
      await setupApiMocks(page);
      const dashboardPage = new PortalDashboardPage(page);
      await dashboardPage.navigate();
      await expectLoadingComplete(page);

      const sidebar = page.locator("aside").first();
      await expect(sidebar.getByRole("link", { name: /help|support/i }).first()).toBeVisible();
    });
  });

  test.describe("Portal Billing", () => {
    test("should load billing page", async ({ page }) => {
      await setupApiMocks(page);
      const billingPage = new PortalBillingPage(page);
      await billingPage.navigate();
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/billing/);
    });

    test("should display current plan information", async ({ page }) => {
      await setupApiMocks(page);
      const billingPage = new PortalBillingPage(page);
      await billingPage.navigate();
      await expectLoadingComplete(page);

      // Should have plan info displayed
      await expect(page.getByRole("heading", { name: /plan features/i })).toBeVisible();
    });

    test("should display invoices section", async ({ page }) => {
      await setupApiMocks(page);
      const billingPage = new PortalBillingPage(page);
      await billingPage.navigate();
      await expectLoadingComplete(page);

      await expect(billingPage.invoicesTable.or(page.locator('[data-testid="invoices"]'))).toBeVisible();
    });
  });

  test.describe("Portal Settings", () => {
    test("should load settings page", async ({ page }) => {
      await setupApiMocks(page);
      const settingsPage = new PortalSettingsPage(page);
      await settingsPage.navigate();
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/settings/);
    });

    test("should display profile settings", async ({ page }) => {
      await setupApiMocks(page);
      const settingsPage = new PortalSettingsPage(page);
      await settingsPage.navigate();
      await expectLoadingComplete(page);

      const nameField = page
        .locator('label:has-text("Organization Name")')
        .locator("..")
        .locator("input")
        .first();
      await expect(nameField).toBeVisible();
    });

    test("should have save button", async ({ page }) => {
      await setupApiMocks(page);
      const settingsPage = new PortalSettingsPage(page);
      await settingsPage.navigate();
      await expectLoadingComplete(page);

      await expect(settingsPage.saveButton).toBeVisible();
    });
  });

  test.describe("Portal Team", () => {
    test("should load team page", async ({ page }) => {
      await setupApiMocks(page);
      const teamPage = new PortalTeamPage(page);
      await teamPage.navigate();
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/team/);
    });

    test("should have invite button", async ({ page }) => {
      await setupApiMocks(page);
      const teamPage = new PortalTeamPage(page);
      await teamPage.navigate();
      await expectLoadingComplete(page);

      await expect(teamPage.inviteButton).toBeVisible();
    });

    test("should display team members table", async ({ page }) => {
      await setupApiMocks(page);
      const teamPage = new PortalTeamPage(page);
      await teamPage.navigate();
      await expectLoadingComplete(page);

      await expect(page.getByRole("heading", { name: "Team Members", level: 1 })).toBeVisible();
      await expect(page.getByText(/alex@acme\.com/i)).toBeVisible();
    });
  });

  test.describe("Portal Usage", () => {
    test("should load usage page", async ({ page }) => {
      await setupApiMocks(page);
      const usagePage = new PortalUsagePage(page);
      await usagePage.navigate();
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/usage/);
    });

    test("should display usage metrics", async ({ page }) => {
      await setupApiMocks(page);
      const usagePage = new PortalUsagePage(page);
      await usagePage.navigate();
      await expectLoadingComplete(page);

      // Should have usage data displayed
      await expect(page.getByRole("heading", { name: /usage by feature/i })).toBeVisible();
      await expect(page.getByRole("heading", { name: /usage by team member/i })).toBeVisible();
    });
  });
});

test.describe("Portal Pages Smoke Tests", () => {
  test.describe("Public Pages", () => {
    const publicPages = STATIC_PORTAL_ROUTES.filter((p) => !p.requiresAuth);

    for (const pageInfo of publicPages) {
      test(`should load ${pageInfo.name} (${pageInfo.path})`, async ({ page }) => {
        await page.goto(pageInfo.path);
        await expectLoadingComplete(page);

        await expect(page).toHaveURL(new RegExp(pageInfo.path.replace(/\//g, "\\/")));
        await expect(page.locator("main, #main-content, .min-h-screen").first()).toBeVisible();
      });
    }
  });

  test.describe("Authenticated Pages", () => {
    test.use({ storageState: "playwright/.auth/tenant.json" });

    const authPages = STATIC_PORTAL_ROUTES.filter((p) => p.requiresAuth);

    for (const pageInfo of authPages) {
      test(`should load ${pageInfo.name} (${pageInfo.path})`, async ({ page }) => {
        await setupApiMocks(page);
        await page.goto(pageInfo.path);
        await expectLoadingComplete(page);

        await expect(page.locator("main, #main-content").first()).toBeVisible();
      });
    }
  });
});
