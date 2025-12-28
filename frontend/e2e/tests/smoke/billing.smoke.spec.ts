import { test, expect } from "../../fixtures";
import { BillingPage, InvoicesPage, SubscriptionsPage } from "../../pages/dashboard";
import { expectLoadingComplete, expectNoErrors } from "../../utils/assertions";
import { setupApiMocks } from "../../utils/api-mocks";
import { STATIC_DASHBOARD_ROUTES } from "../../utils/test-data";

test.describe("Billing Smoke Tests", () => {
  test.use({ storageState: "playwright/.auth/admin.json" });

  test.describe("Billing Dashboard", () => {
    test("should load billing dashboard", async ({ page }) => {
      await setupApiMocks(page);
      const billingPage = new BillingPage(page);
      await billingPage.navigate();
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/billing/);
      await expectNoErrors(page);
    });

    test("should display KPI cards", async ({ page }) => {
      await setupApiMocks(page);
      const billingPage = new BillingPage(page);
      await billingPage.navigate();
      await expectLoadingComplete(page);

      // Should have revenue metrics displayed
      const metricsSection = page.locator('[data-testid="billing-metrics"], .card, .grid').first();
      await expect(metricsSection).toBeVisible();
    });

    test("should have create invoice action", async ({ page }) => {
      await setupApiMocks(page);
      const billingPage = new BillingPage(page);
      await billingPage.navigate();
      await expectLoadingComplete(page);

      await expect(billingPage.createInvoiceButton).toBeVisible();
    });

    test("should navigate to invoices list", async ({ page }) => {
      await setupApiMocks(page);
      const billingPage = new BillingPage(page);
      await billingPage.navigate();
      await expectLoadingComplete(page);

      await billingPage.goToInvoices();

      await expect(page).toHaveURL(/invoices/);
    });
  });

  test.describe("Invoices", () => {
    test("should load invoices page", async ({ page }) => {
      await setupApiMocks(page);
      const invoicesPage = new InvoicesPage(page);
      await invoicesPage.navigate();
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/invoices/);
      // Check for heading - may be h1 or page title
      const heading = page.getByRole("heading", { name: /invoices/i }).or(
        page.locator("h1.page-title")
      );
      await expect(heading.first()).toBeVisible();
    });

    test("should display invoices table", async ({ page }) => {
      await setupApiMocks(page);
      const invoicesPage = new InvoicesPage(page);
      await invoicesPage.navigate();
      await expectLoadingComplete(page);

      await expect(
        invoicesPage.invoicesTable.or(page.getByText(/no invoices found/i))
      ).toBeVisible();
    });

    test("should have search functionality", async ({ page }) => {
      await setupApiMocks(page);
      const invoicesPage = new InvoicesPage(page);
      await invoicesPage.navigate();
      await expectLoadingComplete(page);

      await expect(invoicesPage.searchInput).toBeVisible();
    });

    test("should have create invoice button", async ({ page }) => {
      await setupApiMocks(page);
      const invoicesPage = new InvoicesPage(page);
      await invoicesPage.navigate();
      await expectLoadingComplete(page);

      await expect(invoicesPage.createButton).toBeVisible();
    });

    test("should navigate to create invoice", async ({ page }) => {
      await setupApiMocks(page);
      const invoicesPage = new InvoicesPage(page);
      await invoicesPage.navigate();
      await expectLoadingComplete(page);

      await invoicesPage.goToCreateInvoice();

      await expect(page).toHaveURL(/invoices\/new/);
    });
  });

  test.describe("Create Invoice", () => {
    test("should load create invoice page", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/billing/invoices/new");
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/invoices\/new/);
    });

    test("should display invoice form", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/billing/invoices/new");
      await expectLoadingComplete(page);

      // Should have form elements
      await expect(page.locator("form, [data-testid='invoice-form']").first()).toBeVisible();
    });
  });

  test.describe("Subscriptions", () => {
    test("should load subscriptions page", async ({ page }) => {
      await setupApiMocks(page);
      const subscriptionsPage = new SubscriptionsPage(page);
      await subscriptionsPage.navigate();
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/subscriptions/);
    });

    test("should display subscriptions table", async ({ page }) => {
      await setupApiMocks(page);
      const subscriptionsPage = new SubscriptionsPage(page);
      await subscriptionsPage.navigate();
      await expectLoadingComplete(page);

      // Table or empty state should be visible
      await expect(
        subscriptionsPage.subscriptionsTable.or(page.getByText(/no subscriptions/i))
      ).toBeVisible();
    });
  });

  test.describe("Billing Sub-pages", () => {
    const billingPages = STATIC_DASHBOARD_ROUTES.filter((route) =>
      route.path.startsWith("/billing")
    );

    for (const pageInfo of billingPages) {
      test(`should load ${pageInfo.name} page`, async ({ page }) => {
        await setupApiMocks(page);
        await page.goto(pageInfo.path);
        await expectLoadingComplete(page);

        await expect(page).toHaveURL(new RegExp(pageInfo.path));

        // Main content should be visible
        await expect(page.locator("main, #main-content").first()).toBeVisible();
      });
    }
  });

  test.describe("Dunning Campaigns", () => {
    test("should load dunning campaigns list", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/billing/dunning/campaigns");
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/dunning\/campaigns/);
    });

    test("should navigate to create dunning campaign", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/billing/dunning/campaigns");
      await expectLoadingComplete(page);

      const createButton = page.getByRole("link", { name: /create|new/i }).first();
      if (await createButton.isVisible()) {
        await createButton.click();
        await expect(page).toHaveURL(/dunning\/campaigns\/new/);
      }
    });
  });
});
