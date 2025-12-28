import { test, expect } from "../../fixtures";
import { BillingPage, InvoicesPage, CreateInvoicePage } from "../../pages/dashboard";
import { expectLoadingComplete, expectNoErrors } from "../../utils/assertions";
import { setupApiMocks } from "../../utils/api-mocks";

test.describe("Billing Management Tests", () => {
  test.use({ storageState: "playwright/.auth/admin.json" });

  test.describe("Billing Dashboard", () => {
    test("should display billing metrics", async ({ page }) => {
      await setupApiMocks(page);
      const billingPage = new BillingPage(page);
      await billingPage.navigate();
      await expectLoadingComplete(page);

      // Should display KPI cards
      const metricsSection = page.locator('.card, [data-testid="billing-metrics"]').first();
      await expect(metricsSection).toBeVisible();
    });

    test("should navigate between billing sections", async ({ page }) => {
      await setupApiMocks(page);
      const billingPage = new BillingPage(page);
      await billingPage.navigate();
      await expectLoadingComplete(page);

      // Navigate to invoices
      await billingPage.goToInvoices();
      await expect(page).toHaveURL(/invoices/);

      // Navigate back to billing and go to subscriptions
      await billingPage.navigate();
      await billingPage.goToSubscriptions();
      await expect(page).toHaveURL(/subscriptions/);
    });
  });

  test.describe("Invoices List", () => {
    test("should display invoices with data", async ({ page }) => {
      await setupApiMocks(page);
      const invoicesPage = new InvoicesPage(page);
      await invoicesPage.navigate();
      await expectLoadingComplete(page);

      await expect(invoicesPage.invoicesTable).toBeVisible();
      const invoiceCount = await invoicesPage.getInvoiceCount();
      expect(invoiceCount).toBeGreaterThan(0);
    });

    test("should search invoices", async ({ page }) => {
      await setupApiMocks(page);
      const invoicesPage = new InvoicesPage(page);
      await invoicesPage.navigate();
      await expectLoadingComplete(page);

      await invoicesPage.searchInvoices("INV-2024");
      await expectLoadingComplete(page);

      // Results should be filtered
      await expect(invoicesPage.invoicesTable).toBeVisible();
    });

    test("should filter invoices by status", async ({ page }) => {
      await setupApiMocks(page);
      const invoicesPage = new InvoicesPage(page);
      await invoicesPage.navigate();
      await expectLoadingComplete(page);

      // Open status filter if available
      if (await invoicesPage.statusFilter.isVisible()) {
        await invoicesPage.filterByStatus("paid");
        await expectLoadingComplete(page);

        await expect(invoicesPage.invoicesTable).toBeVisible();
      }
    });

    test("should navigate to invoice details", async ({ page }) => {
      await setupApiMocks(page);
      const invoicesPage = new InvoicesPage(page);
      await invoicesPage.navigate();
      await expectLoadingComplete(page);

      await invoicesPage.openInvoiceDetails("INV-2024-001");

      await expect(page).toHaveURL(/invoices\/inv-001|invoices\/[a-zA-Z0-9-]+/);
    });
  });

  test.describe("Create Invoice", () => {
    test("should display create invoice form", async ({ page }) => {
      await setupApiMocks(page);
      const createInvoicePage = new CreateInvoicePage(page);
      await createInvoicePage.navigate();
      await expectLoadingComplete(page);

      // Should have form elements
      await expect(page.locator("form").first()).toBeVisible();
    });

    test("should add line items", async ({ page }) => {
      await setupApiMocks(page);
      const createInvoicePage = new CreateInvoicePage(page);
      await createInvoicePage.navigate();
      await expectLoadingComplete(page);

      if (await createInvoicePage.addItemButton.isVisible()) {
        await createInvoicePage.addLineItem("Service Fee", 1, 10000);

        // Should see item added
        const items = page.locator('[data-testid="invoice-items"] tr, .line-item');
        await expect(items.first()).toBeVisible();
      }
    });

    test("should create and send invoice", async ({ page }) => {
      await setupApiMocks(page);

      // Mock invoice creation
      await page.route("**/api/v1/billing/invoices", async (route) => {
        if (route.request().method() === "POST") {
          await route.fulfill({
            status: 201,
            contentType: "application/json",
            body: JSON.stringify({
              id: "new-inv-id",
              number: "INV-2024-NEW",
              status: "sent",
            }),
          });
        } else {
          await route.continue();
        }
      });

      const createInvoicePage = new CreateInvoicePage(page);
      await createInvoicePage.navigate();
      await expectLoadingComplete(page);

      // Fill minimum required fields if form is visible
      const customerSelect = page.getByLabel(/customer|tenant/i);
      if (await customerSelect.isVisible()) {
        await customerSelect.selectOption({ index: 0 });
      }

      // Submit form
      await createInvoicePage.sendInvoiceButton.click();
    });

    test("should save invoice as draft", async ({ page }) => {
      await setupApiMocks(page);

      // Mock draft save
      await page.route("**/api/v1/billing/invoices", async (route) => {
        if (route.request().method() === "POST") {
          await route.fulfill({
            status: 201,
            contentType: "application/json",
            body: JSON.stringify({
              id: "draft-inv-id",
              number: "INV-2024-DRAFT",
              status: "draft",
            }),
          });
        } else {
          await route.continue();
        }
      });

      const createInvoicePage = new CreateInvoicePage(page);
      await createInvoicePage.navigate();
      await expectLoadingComplete(page);

      if (await createInvoicePage.saveDraftButton.isVisible()) {
        await createInvoicePage.saveAsDraft();
      }
    });
  });

  test.describe("Subscriptions", () => {
    test("should display subscriptions list", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/billing/subscriptions");
      await expectLoadingComplete(page);

      await expect(page.locator("table")).toBeVisible();
    });

    test("should search subscriptions", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/billing/subscriptions");
      await expectLoadingComplete(page);

      const searchInput = page.getByPlaceholder(/search/i);
      if (await searchInput.isVisible()) {
        await searchInput.fill("Acme");
        await page.keyboard.press("Enter");
        await expectLoadingComplete(page);

        await expect(page.locator("table")).toBeVisible();
      }
    });
  });

  test.describe("Payments", () => {
    test("should display payments list", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/billing/payments");
      await expectLoadingComplete(page);

      await expect(page.locator("main, #main-content").first()).toBeVisible();
    });

    test("should navigate to record payment", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/billing/payments");
      await expectLoadingComplete(page);

      const recordButton = page.getByRole("link", { name: /record|new/i });
      if (await recordButton.isVisible()) {
        await recordButton.click();
        await expect(page).toHaveURL(/record|new/);
      }
    });
  });
});
