import { test, expect } from "../../fixtures";
import { expectLoadingComplete } from "../../utils/assertions";
import { setupApiMocks } from "../../utils/api-mocks";
import {
  DYNAMIC_ROUTES,
  TEST_FIXTURES,
  resolveDynamicRoute,
} from "../../utils/test-data";

/**
 * Dynamic Route Smoke Tests
 * Tests that all dynamic routes render without critical errors
 */
test.describe("Dynamic Routes Smoke Tests", () => {
  test.use({ storageState: "playwright/.auth/admin.json" });

  // Group routes by category for better organization
  const dashboardDynamicRoutes = DYNAMIC_ROUTES.filter(
    (r) => r.group === "dashboard"
  );

  test.describe("Dashboard Dynamic Routes", () => {
    for (const route of dashboardDynamicRoutes) {
      test(`should load ${route.name} (${route.path})`, async ({ page }) => {
        await setupApiMocks(page);

        // Resolve dynamic segments with test fixtures
        const resolvedPath = resolveDynamicRoute(route.path, TEST_FIXTURES);
        await page.goto(resolvedPath);

        await page.waitForLoadState("domcontentloaded");
        await expectLoadingComplete(page);

        // Main content should be visible
        const mainContent = page.locator("main, #main-content, [role='main']");
        await expect(mainContent.first()).toBeVisible();

        // Should not have critical error boundary
        const criticalError = page.locator(
          '[data-testid="critical-error"], .error-boundary'
        );
        await expect(criticalError).not.toBeVisible();
      });
    }
  });

  test.describe("Specific Dynamic Route Tests", () => {
    test("should load user detail page with user data", async ({ page }) => {
      await setupApiMocks(page);

      // Mock specific user endpoint
      await page.route("**/api/v1/users/user-001", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: "user-001",
            email: "admin@test.local",
            name: "Test Admin",
            role: "admin",
            status: "active",
            createdAt: new Date().toISOString(),
          }),
        });
      });

      await page.goto("/users/user-001");
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/users\/user-001/);
      await expect(page.locator("main, #main-content").first()).toBeVisible();
    });

    test("should load tenant detail page with tenant data", async ({
      page,
    }) => {
      await setupApiMocks(page);

      // Mock specific tenant endpoint
      await page.route("**/api/v1/tenants/tenant-001", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: "tenant-001",
            name: "Acme Corporation",
            domain: "acme.local",
            status: "active",
            plan: "professional",
            userCount: 15,
            createdAt: new Date().toISOString(),
          }),
        });
      });

      await page.goto("/tenants/tenant-001");
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/tenants\/tenant-001/);
      await expect(page.locator("main, #main-content").first()).toBeVisible();
    });

    test("should load invoice detail page", async ({ page }) => {
      await setupApiMocks(page);

      // Mock specific invoice endpoint
      await page.route("**/api/v1/billing/invoices/inv-001", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: "inv-001",
            number: "INV-2024-001",
            customer: {
              id: "cust-001",
              name: "Acme Corp",
              email: "billing@acme.com",
            },
            amount: 125000,
            status: "paid",
            currency: "USD",
            dueDate: new Date().toISOString(),
            createdAt: new Date().toISOString(),
            lineItems: [
              {
                description: "Pro plan",
                quantity: 1,
                unitPrice: 125000,
                amount: 125000,
              },
            ],
          }),
        });
      });

      await page.goto("/billing/invoices/inv-001");
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/invoices\/inv-001/);
      await expect(page.locator("main, #main-content").first()).toBeVisible();
    });

    test("should load subscription detail page", async ({ page }) => {
      await setupApiMocks(page);

      await page.route(
        "**/api/v1/billing/subscriptions/sub-001",
        async (route) => {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
              id: "sub-001",
              customerId: "cust-001",
              customerName: "Acme Corp",
              planName: "Professional",
              status: "active",
              currentPeriodEnd: new Date(
                Date.now() + 30 * 24 * 60 * 60 * 1000
              ).toISOString(),
              amount: 9900,
            }),
          });
        }
      );

      await page.goto("/billing/subscriptions/sub-001");
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/subscriptions\/sub-001/);
    });

    test("should load job detail page", async ({ page }) => {
      await setupApiMocks(page);

      await page.route("**/api/v1/jobs/job-001", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: "job-001",
            name: "Daily backup",
            status: "completed",
            type: "scheduled",
            lastRunAt: new Date().toISOString(),
            nextRunAt: new Date(
              Date.now() + 24 * 60 * 60 * 1000
            ).toISOString(),
            logs: [],
          }),
        });
      });

      await page.goto("/jobs/job-001");
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/jobs\/job-001/);
    });

    test("should load workflow detail page", async ({ page }) => {
      await setupApiMocks(page);

      await page.route("**/api/v1/workflows/workflow-001", async (route) => {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: "workflow-001",
            name: "Onboarding",
            status: "active",
            executionCount: 42,
            steps: [],
            createdAt: new Date().toISOString(),
          }),
        });
      });

      await page.goto("/workflows/workflow-001");
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/workflows\/workflow-001/);
    });

    test("should load dunning campaign detail page", async ({ page }) => {
      await setupApiMocks(page);

      await page.route(
        "**/api/v1/billing/dunning/campaigns/camp-001",
        async (route) => {
          await route.fulfill({
            status: 200,
            contentType: "application/json",
            body: JSON.stringify({
              id: "camp-001",
              name: "Default Dunning",
              status: "active",
              steps: [
                { day: 1, action: "email", template: "reminder_1" },
                { day: 7, action: "email", template: "reminder_2" },
              ],
              createdAt: new Date().toISOString(),
            }),
          });
        }
      );

      await page.goto("/billing/dunning/campaigns/camp-001");
      await expectLoadingComplete(page);

      await expect(page).toHaveURL(/dunning\/campaigns\/camp-001/);
    });
  });

  test.describe("Dynamic Route Error Handling", () => {
    test("should handle 404 for non-existent user", async ({ page }) => {
      await setupApiMocks(page);

      await page.route("**/api/v1/users/non-existent", async (route) => {
        await route.fulfill({
          status: 404,
          contentType: "application/json",
          body: JSON.stringify({
            error_code: "NOT_FOUND",
            message: "User not found",
          }),
        });
      });

      await page.goto("/users/non-existent");
      await expectLoadingComplete(page);

      // Should show error or not found state
      const errorOrNotFound = page.locator(
        '[data-testid="error"], [data-testid="not-found"], text=/not found/i'
      );
      await expect(errorOrNotFound.first()).toBeVisible();
    });

    test("should handle 404 for non-existent invoice", async ({ page }) => {
      await setupApiMocks(page);

      await page.route(
        "**/api/v1/billing/invoices/non-existent",
        async (route) => {
          await route.fulfill({
            status: 404,
            contentType: "application/json",
            body: JSON.stringify({
              error_code: "NOT_FOUND",
              message: "Invoice not found",
            }),
          });
        }
      );

      await page.goto("/billing/invoices/non-existent");
      await expectLoadingComplete(page);

      const errorOrNotFound = page.locator(
        '[data-testid="error"], [data-testid="not-found"], text=/not found/i'
      );
      await expect(errorOrNotFound.first()).toBeVisible();
    });
  });
});
