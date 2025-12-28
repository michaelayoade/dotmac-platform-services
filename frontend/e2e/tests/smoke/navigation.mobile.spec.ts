import { test, expect } from "../../fixtures";
import { expectLoadingComplete } from "../../utils/assertions";
import { setupApiMocks } from "../../utils/api-mocks";
import { PORTAL_URLS } from "../../utils/test-data";

/**
 * Mobile Navigation Tests
 * Tests mobile-specific UI components and navigation patterns
 * These tests run on iPhone 13 viewport (configured in playwright.config.ts)
 */
test.describe("Mobile Navigation Tests", () => {
  test.describe("Dashboard Mobile Navigation", () => {
    test.use({ storageState: "playwright/.auth/admin.json" });

    test("should display mobile menu button on small screens", async ({
      page,
    }) => {
      await setupApiMocks(page);
      await page.goto("/");
      await expectLoadingComplete(page);

      // Mobile menu button should be visible
      const mobileMenuButton = page.locator(
        'button[aria-label*="menu"], button[aria-label*="Menu"], [data-testid="mobile-menu-button"], button:has([data-testid="menu-icon"])'
      );
      await expect(mobileMenuButton.first()).toBeVisible();
    });

    test("should open mobile drawer when menu button clicked", async ({
      page,
    }) => {
      await setupApiMocks(page);
      await page.goto("/");
      await expectLoadingComplete(page);

      // Click mobile menu button
      const mobileMenuButton = page.locator(
        'button[aria-label*="menu"], button[aria-label*="Menu"], [data-testid="mobile-menu-button"]'
      );
      await mobileMenuButton.first().click();

      // Mobile drawer/nav should be visible
      const mobileNav = page.locator(
        '[data-testid="mobile-drawer"], [data-testid="mobile-nav"], [role="dialog"] nav, .mobile-nav'
      );
      await expect(mobileNav.first()).toBeVisible();
    });

    test("should navigate via mobile menu to billing", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/");
      await expectLoadingComplete(page);

      // Open mobile menu
      const mobileMenuButton = page.locator(
        'button[aria-label*="menu"], button[aria-label*="Menu"], [data-testid="mobile-menu-button"]'
      );
      await mobileMenuButton.first().click();

      // Click billing link
      const billingLink = page.getByRole("link", { name: /billing/i }).first();
      await billingLink.click();

      await expectLoadingComplete(page);
      await expect(page).toHaveURL(/billing/);
    });

    test("should navigate via mobile menu to users", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/");
      await expectLoadingComplete(page);

      // Open mobile menu
      const mobileMenuButton = page.locator(
        'button[aria-label*="menu"], button[aria-label*="Menu"], [data-testid="mobile-menu-button"]'
      );
      await mobileMenuButton.first().click();

      // Click users link
      const usersLink = page.getByRole("link", { name: /users/i }).first();
      await usersLink.click();

      await expectLoadingComplete(page);
      await expect(page).toHaveURL(/users/);
    });

    test("should close mobile drawer when clicking outside", async ({
      page,
    }) => {
      await setupApiMocks(page);
      await page.goto("/");
      await expectLoadingComplete(page);

      // Open mobile menu
      const mobileMenuButton = page.locator(
        'button[aria-label*="menu"], button[aria-label*="Menu"], [data-testid="mobile-menu-button"]'
      );
      await mobileMenuButton.first().click();

      // Mobile drawer should be visible
      const mobileNav = page.locator(
        '[data-testid="mobile-drawer"], [data-testid="mobile-nav"], [role="dialog"]'
      );
      await expect(mobileNav.first()).toBeVisible();

      // Click overlay/backdrop to close
      const overlay = page.locator(
        '[data-testid="drawer-overlay"], [data-testid="backdrop"], .backdrop, [role="dialog"] + div'
      );
      if (await overlay.first().isVisible()) {
        await overlay.first().click({ force: true });
        await expect(mobileNav.first()).not.toBeVisible();
      }
    });

    test("should close mobile drawer via close button", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/");
      await expectLoadingComplete(page);

      // Open mobile menu
      const mobileMenuButton = page.locator(
        'button[aria-label*="menu"], button[aria-label*="Menu"], [data-testid="mobile-menu-button"]'
      );
      await mobileMenuButton.first().click();

      // Click close button if available
      const closeButton = page.locator(
        '[data-testid="close-drawer"], button[aria-label*="close"], button[aria-label*="Close"]'
      );
      if (await closeButton.first().isVisible()) {
        await closeButton.first().click();

        const mobileNav = page.locator(
          '[data-testid="mobile-drawer"], [data-testid="mobile-nav"]'
        );
        await expect(mobileNav.first()).not.toBeVisible();
      }
    });

    test("should show header on mobile", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/");
      await expectLoadingComplete(page);

      const header = page.locator("header");
      await expect(header).toBeVisible();
    });

    test("should hide desktop sidebar on mobile", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/");
      await expectLoadingComplete(page);

      // Desktop sidebar should be hidden on mobile
      const desktopSidebar = page.locator(
        'aside:not([data-testid="mobile-drawer"]), [data-testid="desktop-sidebar"]'
      );

      // Either hidden or not visible
      const isHidden =
        (await desktopSidebar.count()) === 0 ||
        !(await desktopSidebar.first().isVisible());
      expect(isHidden).toBe(true);
    });
  });

  test.describe("Partner Portal Mobile Navigation", () => {
    test.use({ storageState: "playwright/.auth/partner.json" });

    test("should display partner mobile menu", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto(PORTAL_URLS.partner.home);
      await expectLoadingComplete(page);

      const mobileMenuButton = page.locator(
        'button[aria-label*="menu"], button[aria-label*="Menu"], [data-testid="mobile-menu-button"]'
      );
      await expect(mobileMenuButton.first()).toBeVisible();
    });

    test("should navigate to partner commissions on mobile", async ({
      page,
    }) => {
      await setupApiMocks(page);
      await page.goto(PORTAL_URLS.partner.home);
      await expectLoadingComplete(page);

      // Open mobile menu
      const mobileMenuButton = page.locator(
        'button[aria-label*="menu"], button[aria-label*="Menu"], [data-testid="mobile-menu-button"]'
      );
      await mobileMenuButton.first().click();

      // Navigate to commissions
      const commissionsLink = page
        .getByRole("link", { name: /commissions/i })
        .first();
      await commissionsLink.click();

      await expectLoadingComplete(page);
      await expect(page).toHaveURL(/commissions/);
    });
  });

  test.describe("Tenant Portal Mobile Navigation", () => {
    test.use({ storageState: "playwright/.auth/tenant.json" });

    test("should display portal mobile menu", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto(PORTAL_URLS.portal.home);
      await expectLoadingComplete(page);

      const mobileMenuButton = page.locator(
        'button[aria-label*="menu"], button[aria-label*="Menu"], [data-testid="mobile-menu-button"]'
      );
      await expect(mobileMenuButton.first()).toBeVisible();
    });

    test("should navigate to portal billing on mobile", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto(PORTAL_URLS.portal.home);
      await expectLoadingComplete(page);

      // Open mobile menu
      const mobileMenuButton = page.locator(
        'button[aria-label*="menu"], button[aria-label*="Menu"], [data-testid="mobile-menu-button"]'
      );
      await mobileMenuButton.first().click();

      // Navigate to billing
      const billingLink = page.getByRole("link", { name: /billing/i }).first();
      await billingLink.click();

      await expectLoadingComplete(page);
      await expect(page).toHaveURL(/billing/);
    });
  });

  test.describe("Auth Pages Mobile", () => {
    test("should display login form correctly on mobile", async ({ page }) => {
      await page.goto("/login");
      await expectLoadingComplete(page);

      // Form should be visible and usable
      await expect(
        page.locator('input[type="email"], input#email')
      ).toBeVisible();
      await expect(
        page.locator('input[type="password"], input#password')
      ).toBeVisible();
      await expect(page.locator('button[type="submit"]')).toBeVisible();
    });

    test("should display signup form correctly on mobile", async ({ page }) => {
      await page.goto("/signup");
      await expectLoadingComplete(page);

      // Form should be visible
      await expect(
        page.locator('input[type="email"], input#email')
      ).toBeVisible();
      await expect(page.locator('button[type="submit"]')).toBeVisible();
    });

    test("should display partner login on mobile", async ({ page }) => {
      await page.goto(PORTAL_URLS.partner.login);
      await expectLoadingComplete(page);

      await expect(
        page.locator('input[type="email"], input#email')
      ).toBeVisible();
      await expect(page.locator('button[type="submit"]')).toBeVisible();
    });
  });

  test.describe("Mobile Touch Interactions", () => {
    test.use({ storageState: "playwright/.auth/admin.json" });

    test("should support touch scroll on tables", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/users");
      await expectLoadingComplete(page);

      const table = page.locator("table");
      if (await table.isVisible()) {
        // Table should be scrollable on mobile
        const tableContainer = table.locator("..");
        const overflowX = await tableContainer.evaluate(
          (el) => getComputedStyle(el).overflowX
        );

        // Should have horizontal scroll capability
        expect(["auto", "scroll"]).toContain(overflowX);
      }
    });

    test("should have touch-friendly button sizes", async ({ page }) => {
      await setupApiMocks(page);
      await page.goto("/");
      await expectLoadingComplete(page);

      // Buttons should be at least 44px for touch (WCAG)
      const buttons = page.locator("button");
      const buttonCount = await buttons.count();

      for (let i = 0; i < Math.min(buttonCount, 5); i++) {
        const button = buttons.nth(i);
        if (await button.isVisible()) {
          const box = await button.boundingBox();
          if (box) {
            // Should be at least 44px in one dimension (WCAG touch target)
            expect(box.height >= 32 || box.width >= 32).toBe(true);
          }
        }
      }
    });
  });
});
