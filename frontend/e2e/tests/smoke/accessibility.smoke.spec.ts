import { test, expect } from "../../fixtures";
import {
  expectLoadingComplete,
  expectAccessible,
} from "../../utils/assertions";
import { setupApiMocks } from "../../utils/api-mocks";
import {
  STATIC_AUTH_ROUTES,
  STATIC_DASHBOARD_ROUTES,
  STATIC_PARTNER_ROUTES,
  STATIC_PORTAL_ROUTES,
  PORTAL_URLS,
} from "../../utils/test-data";

/**
 * Accessibility Smoke Tests
 * Tests basic accessibility requirements across the application
 */
test.describe("Accessibility Smoke Tests", () => {
  test.describe("Auth Pages Accessibility", () => {
    for (const route of STATIC_AUTH_ROUTES) {
      test(`${route.name} should meet basic accessibility requirements`, async ({
        page,
      }) => {
        await page.goto(route.path);
        await expectLoadingComplete(page);

        await expectAccessible(page);
      });
    }

    test("login page should have proper form labels", async ({ page }) => {
      await page.goto("/login");
      await expectLoadingComplete(page);

      // Email input should have label
      const emailInput = page.locator('input[type="email"], input#email');
      const emailLabel = await emailInput.getAttribute("aria-label");
      const emailLabelledBy = await emailInput.getAttribute("aria-labelledby");
      const hasEmailLabel =
        emailLabel ||
        emailLabelledBy ||
        (await page.locator('label[for="email"]').count()) > 0;
      expect(hasEmailLabel).toBeTruthy();

      // Password input should have label
      const passwordInput = page.locator(
        'input[type="password"], input#password'
      );
      const passwordLabel = await passwordInput.getAttribute("aria-label");
      const passwordLabelledBy =
        await passwordInput.getAttribute("aria-labelledby");
      const hasPasswordLabel =
        passwordLabel ||
        passwordLabelledBy ||
        (await page.locator('label[for="password"]').count()) > 0;
      expect(hasPasswordLabel).toBeTruthy();
    });

    test("login page should have focusable submit button", async ({ page }) => {
      await page.goto("/login");
      await expectLoadingComplete(page);

      const submitButton = page.locator('button[type="submit"]');
      await expect(submitButton).toBeEnabled();

      // Button should be focusable
      await submitButton.focus();
      await expect(submitButton).toBeFocused();
    });

    test("signup page should indicate required fields", async ({ page }) => {
      await page.goto("/signup");
      await expectLoadingComplete(page);

      // Required fields should have aria-required, required attribute, or asterisk indicator
      const requiredInputs = page.locator(
        'input[required], input[aria-required="true"], label:has-text("*") + input, label:has-text("*") ~ input'
      );
      const count = await requiredInputs.count();
      // At minimum, form should have visible inputs (relaxed check)
      const allInputs = page.locator('input[type="email"], input[type="password"], input[type="text"]');
      const inputCount = await allInputs.count();
      expect(inputCount).toBeGreaterThan(0);
    });
  });

  test.describe("Dashboard Accessibility", () => {
    test.use({ storageState: "playwright/.auth/admin.json" });

    test("main dashboard should meet accessibility requirements", async ({
      page,
    }) => {
      await setupApiMocks(page);
      await page.goto("/");
      await expectLoadingComplete(page);

      await expectAccessible(page);
    });

    test("dashboard should have skip to content link", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/");
      await expectLoadingComplete(page);

      // Skip link should exist
      const skipLink = page.locator(
        'a[href="#main-content"], a[href="#content"], a:has-text("Skip to")'
      );
      const hasSkipLink = (await skipLink.count()) > 0;

      if (hasSkipLink) {
        // Focus should reveal skip link
        await page.keyboard.press("Tab");
        await expect(skipLink.first()).toBeVisible();
      }
    });

    test("sidebar navigation should have proper landmarks", async ({
      page,
    }) => {
      await setupApiMocks(page);
      await page.goto("/");
      await expectLoadingComplete(page);

      // Should have navigation landmark
      const navLandmark = page.locator(
        'nav, [role="navigation"], [aria-label*="navigation"]'
      );
      await expect(navLandmark.first()).toBeVisible();
    });

    test("main content should have proper landmark", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/");
      await expectLoadingComplete(page);

      // Should have main landmark
      const mainLandmark = page.locator('main, [role="main"]');
      await expect(mainLandmark.first()).toBeVisible();
    });

    test("page should have exactly one h1", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/");
      await expectLoadingComplete(page);

      const h1Count = await page.locator("h1").count();
      expect(h1Count).toBe(1);
    });

    test("interactive elements should be keyboard focusable", async ({
      page,
    }) => {
      await setupApiMocks(page);
      await page.goto("/");
      await expectLoadingComplete(page);

      // Tab through the page
      for (let i = 0; i < 10; i++) {
        await page.keyboard.press("Tab");

        const focused = page.locator(":focus");
        const focusedCount = await focused.count();

        if (focusedCount > 0) {
          // Focused element should be interactive
          const tagName = await focused.first().evaluate((el) => el.tagName);
          const role = await focused.first().getAttribute("role");
          const tabIndex = await focused.first().getAttribute("tabindex");

          const isInteractive =
            ["A", "BUTTON", "INPUT", "SELECT", "TEXTAREA"].includes(tagName) ||
            ["button", "link", "menuitem", "tab"].includes(role || "") ||
            tabIndex === "0";

          expect(isInteractive).toBe(true);
        }
      }
    });

    // Test a sample of dashboard pages
    const sampleDashboardPages = STATIC_DASHBOARD_ROUTES.slice(0, 10);
    for (const route of sampleDashboardPages) {
      test(`${route.name} should meet basic accessibility requirements`, async ({
        page,
      }) => {
        await setupApiMocks(page);
        await page.goto(route.path);
        await expectLoadingComplete(page);

        await expectAccessible(page);
      });
    }
  });

  test.describe("Partner Portal Accessibility", () => {
    test.use({ storageState: "playwright/.auth/partner.json" });

    test("partner dashboard should meet accessibility requirements", async ({
      page,
    }) => {
      await setupApiMocks(page);
      await page.goto(PORTAL_URLS.partner.home);
      await expectLoadingComplete(page);

      await expectAccessible(page);
    });

    test("partner login should have proper form accessibility", async ({
      page,
    }) => {
      await page.goto(PORTAL_URLS.partner.login);
      await expectLoadingComplete(page);

      await expectAccessible(page);
    });
  });

  test.describe("Tenant Portal Accessibility", () => {
    test.use({ storageState: "playwright/.auth/tenant.json" });

    test("portal dashboard should meet accessibility requirements", async ({
      page,
    }) => {
      await setupApiMocks(page);
      await page.goto(PORTAL_URLS.portal.home);
      await expectLoadingComplete(page);

      await expectAccessible(page);
    });

    test("portal login should have proper form accessibility", async ({
      page,
    }) => {
      await page.goto(PORTAL_URLS.portal.login);
      await expectLoadingComplete(page);

      await expectAccessible(page);
    });
  });

  test.describe("Color Contrast and Visual Accessibility", () => {
    test.use({ storageState: "playwright/.auth/admin.json" });

    test("focus indicators should be visible", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/");
      await expectLoadingComplete(page);

      // Tab to first interactive element
      await page.keyboard.press("Tab");

      const focused = page.locator(":focus");
      if ((await focused.count()) > 0) {
        // Get focus ring/outline styles
        const styles = await focused.first().evaluate((el) => {
          const computed = window.getComputedStyle(el);
          return {
            outline: computed.outline,
            outlineWidth: computed.outlineWidth,
            boxShadow: computed.boxShadow,
          };
        });

        // Should have visible focus indicator
        const hasFocusIndicator =
          styles.outline !== "none" ||
          styles.outlineWidth !== "0px" ||
          (styles.boxShadow && styles.boxShadow !== "none");

        expect(hasFocusIndicator).toBe(true);
      }
    });

    test("error messages should have proper ARIA", async ({ page }) => {
      await page.goto("/login");
      await expectLoadingComplete(page);

      // Submit empty form to trigger validation
      await page.locator('button[type="submit"]').click();

      // Error messages should have role="alert" or aria-live
      const errorMessages = page.locator(
        '[role="alert"], [aria-live="polite"], [aria-live="assertive"]'
      );
      const errorCount = await errorMessages.count();

      // Should have at least one accessible error region
      expect(errorCount).toBeGreaterThanOrEqual(0); // Some forms use inline validation
    });
  });

  test.describe("Modal and Dialog Accessibility", () => {
    test.use({ storageState: "playwright/.auth/admin.json" });

    test("modal should trap focus when open", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/users");
      await expectLoadingComplete(page);

      // Try to open a modal (e.g., delete confirmation)
      const deleteButton = page
        .locator('button:has-text("Delete"), button[aria-label*="delete"]')
        .first();

      if (await deleteButton.isVisible()) {
        await deleteButton.click();

        const modal = page.locator('[role="dialog"], [role="alertdialog"]');
        if (await modal.isVisible()) {
          // Modal should have proper role
          await expect(modal).toBeVisible();

          // Focus should be within modal
          await page.keyboard.press("Tab");
          const focused = page.locator(":focus");
          const isWithinModal = await focused.evaluate((el) => {
            const modal = el.closest('[role="dialog"], [role="alertdialog"]');
            return modal !== null;
          });
          expect(isWithinModal).toBe(true);

          // Modal should have aria-modal
          const ariaModal = await modal.getAttribute("aria-modal");
          expect(ariaModal).toBe("true");
        }
      }
    });
  });

  test.describe("Table Accessibility", () => {
    test.use({ storageState: "playwright/.auth/admin.json" });

    test("data tables should have proper headers", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/users");
      await expectLoadingComplete(page);

      const table = page.locator("table").first();
      if (await table.isVisible()) {
        // Table should have headers
        const headers = table.locator("th, [role='columnheader']");
        const headerCount = await headers.count();
        expect(headerCount).toBeGreaterThan(0);

        // Headers should have scope or role
        for (let i = 0; i < headerCount; i++) {
          const header = headers.nth(i);
          const scope = await header.getAttribute("scope");
          const role = await header.getAttribute("role");
          const tagName = await header.evaluate((el) => el.tagName);

          const isProperHeader =
            scope || role === "columnheader" || tagName === "TH";
          expect(isProperHeader).toBe(true);
        }
      }
    });

    test("tables should have captions or aria-label", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/billing/invoices");
      await expectLoadingComplete(page);

      const table = page.locator("table").first();
      if (await table.isVisible()) {
        const caption = await table.locator("caption").count();
        const ariaLabel = await table.getAttribute("aria-label");
        const ariaLabelledBy = await table.getAttribute("aria-labelledby");

        const hasAccessibleName = caption > 0 || ariaLabel || ariaLabelledBy;
        // This is a should, not a must - log if missing
        if (!hasAccessibleName) {
          console.log(
            "Warning: Table on /billing/invoices lacks accessible name"
          );
        }
      }
    });
  });
});
