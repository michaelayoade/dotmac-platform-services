import { test, expect } from "../../fixtures";
import {
  PartnerLoginPage,
  PartnerApplyPage,
  PartnerDashboardPage,
  PartnerCommissionsPage,
  PartnerReferralsPage,
  PartnerStatementsPage,
  PartnerTeamPage,
  PartnerSettingsPage,
} from "../../pages/partner";
import { expectLoadingComplete, expectNoErrors } from "../../utils/assertions";
import { STATIC_PARTNER_ROUTES } from "../../utils/test-data";
import { setupApiMocks } from "../../utils/api-mocks";

test.describe("Partner Portal Smoke Tests", () => {
  test.describe("Partner Login", () => {
    test("should display partner login page", async ({ page }) => {
      const partnerLoginPage = new PartnerLoginPage(page);
      await partnerLoginPage.navigate();

      await expect(partnerLoginPage.emailInput).toBeVisible();
      await expect(partnerLoginPage.passwordInput).toBeVisible();
      await expect(partnerLoginPage.submitButton).toBeVisible();
    });

    test("should have partner branding", async ({ page }) => {
      const partnerLoginPage = new PartnerLoginPage(page);
      await partnerLoginPage.navigate();

      // Should have partner-specific branding
      await expect(page.getByText("Partner Portal", { exact: true })).toBeVisible();
    });

    test("should have link to partner application", async ({ page }) => {
      const partnerLoginPage = new PartnerLoginPage(page);
      await partnerLoginPage.navigate();

      await expect(partnerLoginPage.applyLink).toBeVisible();
    });
  });

  test.describe("Partner Application", () => {
    test("should display partner application form", async ({ page }) => {
      const applyPage = new PartnerApplyPage(page);
      await applyPage.navigate();

      await expect(applyPage.companyNameInput).toBeVisible();
      await expect(applyPage.emailInput).toBeVisible();
      await expect(applyPage.submitButton).toBeVisible();
    });

    test("should have terms checkbox", async ({ page }) => {
      const applyPage = new PartnerApplyPage(page);
      await applyPage.navigate();

      await expect(page.getByText(/terms of service/i)).toBeVisible();
    });
  });
});

test.describe("Partner Portal Authenticated", () => {
  test.use({ storageState: "playwright/.auth/partner.json" });

  test.describe("Partner Dashboard", () => {
    test("should load partner dashboard", async ({ page }) => {
      await setupApiMocks(page);
      const dashboardPage = new PartnerDashboardPage(page);
      await dashboardPage.navigate();
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/partner/);
      await expectNoErrors(page);
    });

    test("should display partner stats", async ({ page }) => {
      await setupApiMocks(page);
      const dashboardPage = new PartnerDashboardPage(page);
      await dashboardPage.navigate();
      await expectLoadingComplete(page);

      // Should have some stats displayed
      await expect(page.getByText(/total revenue generated/i)).toBeVisible();
    });

    test("should have navigation links", async ({ page }) => {
      await setupApiMocks(page);
      const dashboardPage = new PartnerDashboardPage(page);
      await dashboardPage.navigate();
      await expectLoadingComplete(page);

      // Should have key navigation
      const sidebar = page.locator("aside").first();
      await expect(sidebar.getByRole("link", { name: /commissions/i }).first()).toBeVisible();
      await expect(sidebar.getByRole("link", { name: /referrals/i }).first()).toBeVisible();
    });
  });

  test.describe("Partner Commissions", () => {
    test("should load commissions page", async ({ page }) => {
      await setupApiMocks(page);
      const commissionsPage = new PartnerCommissionsPage(page);
      await commissionsPage.navigate();
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/commissions/);
    });

    test("should display commissions data", async ({ page }) => {
      await setupApiMocks(page);
      const commissionsPage = new PartnerCommissionsPage(page);
      await commissionsPage.navigate();
      await expectLoadingComplete(page);

      // Should have table or list
      await expect(
        commissionsPage.commissionsTable
          .or(page.getByText(/no commissions/i))
          .or(page.locator('[data-testid="commissions-list"]'))
      ).toBeVisible();
    });
  });

  test.describe("Partner Referrals", () => {
    test("should load referrals page", async ({ page }) => {
      await setupApiMocks(page);
      const referralsPage = new PartnerReferralsPage(page);
      await referralsPage.navigate();
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/referrals/);
    });

    test("should have new referral button", async ({ page }) => {
      await setupApiMocks(page);
      const referralsPage = new PartnerReferralsPage(page);
      await referralsPage.navigate();
      await expectLoadingComplete(page);

      await expect(referralsPage.newReferralButton).toBeVisible();
    });
  });

  test.describe("Partner Statements", () => {
    test("should load statements page", async ({ page }) => {
      await setupApiMocks(page);
      const statementsPage = new PartnerStatementsPage(page);
      await statementsPage.navigate();
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/statements/);
    });
  });

  test.describe("Partner Team", () => {
    test("should load team page", async ({ page }) => {
      await setupApiMocks(page);
      const teamPage = new PartnerTeamPage(page);
      await teamPage.navigate();
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/team/);
    });

    test("should have invite button", async ({ page }) => {
      await setupApiMocks(page);
      const teamPage = new PartnerTeamPage(page);
      await teamPage.navigate();
      await expectLoadingComplete(page);

      await expect(teamPage.inviteButton).toBeVisible();
    });
  });

  test.describe("Partner Settings", () => {
    test("should load settings page", async ({ page }) => {
      await setupApiMocks(page);
      const settingsPage = new PartnerSettingsPage(page);
      await settingsPage.navigate();
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/settings/);
    });
  });
});

test.describe("Partner Pages Smoke Tests", () => {
  test.describe("Public Pages", () => {
    const publicPages = STATIC_PARTNER_ROUTES.filter((p) => !p.requiresAuth);

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
    test.use({ storageState: "playwright/.auth/partner.json" });

    const authPages = STATIC_PARTNER_ROUTES.filter((p) => p.requiresAuth);

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
