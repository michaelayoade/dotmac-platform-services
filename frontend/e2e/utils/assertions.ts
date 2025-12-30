import { Page, expect, Locator } from "@playwright/test";

/**
 * Custom assertion helpers for E2E tests
 */

/**
 * Assert page has expected title
 */
export async function expectPageTitle(
  page: Page,
  expectedTitle: string | RegExp
): Promise<void> {
  await expect(page).toHaveTitle(expectedTitle);
}

/**
 * Assert current URL matches expected path
 */
export async function expectUrl(page: Page, expectedPath: string): Promise<void> {
  await expect(page).toHaveURL(new RegExp(expectedPath));
}

/**
 * Assert no error alerts are visible on the page
 */
export async function expectNoErrors(page: Page): Promise<void> {
  const mainContent = page.locator("main, #main-content").first();
  const errorAlerts = mainContent.locator(
    '[role="alert"].status-error, .bg-status-error, [data-testid="error"]'
  );
  const errorCount = await errorAlerts.count();

  if (errorCount > 0) {
    const errorText = await errorAlerts.first().textContent();
    throw new Error(`Unexpected error on page: ${errorText}`);
  }
}

/**
 * Assert a success message is visible
 */
export async function expectSuccessMessage(page: Page): Promise<void> {
  const successAlerts = page.locator(
    '[role="alert"].status-success, .bg-status-success, [data-testid="success"]'
  );
  await expect(successAlerts.first()).toBeVisible();
}

/**
 * Assert table has minimum number of rows
 */
export async function expectTableToHaveRows(
  table: Locator,
  minRows: number
): Promise<void> {
  const rowCount = await table.locator("tbody tr").count();
  expect(rowCount).toBeGreaterThanOrEqual(minRows);
}

/**
 * Assert table has expected column headers
 */
export async function expectTableHeaders(
  page: Page,
  headers: string[]
): Promise<void> {
  const tableHeaders = page.locator("table thead th");
  for (const header of headers) {
    await expect(tableHeaders.filter({ hasText: header })).toBeVisible();
  }
}

/**
 * Assert form validation error is displayed for a field
 */
export async function expectFormValidationError(
  page: Page,
  fieldName: string
): Promise<void> {
  const errorMessage = page
    .locator(`[data-error="${fieldName}"], [aria-describedby*="error"]`)
    .first();
  await expect(errorMessage).toBeVisible();
}

/**
 * Wait for all loading spinners to disappear
 */
export async function expectLoadingComplete(page: Page): Promise<void> {
  await page.waitForLoadState("domcontentloaded");

  // Wait for loading spinners to disappear
  await page
    .waitForSelector('.animate-pulse, [data-loading="true"], .loading-skeleton', {
      state: "hidden",
      timeout: 10000,
    })
    .catch(() => {});

  // Best-effort network idle; some pages keep polling in the background.
  await page.waitForLoadState("networkidle", { timeout: 5000 }).catch(() => {});
}

/**
 * Assert breadcrumb trail shows expected crumbs
 */
export async function expectBreadcrumbTrail(
  page: Page,
  ...crumbs: string[]
): Promise<void> {
  const breadcrumb = page.locator('nav[aria-label="Breadcrumb"]');
  for (const crumb of crumbs) {
    await expect(breadcrumb.getByText(crumb)).toBeVisible();
  }
}

/**
 * Assert page heading is visible
 */
export async function expectPageHeading(
  page: Page,
  heading: string | RegExp
): Promise<void> {
  await expect(
    page.getByRole("heading", { name: heading, level: 1 })
  ).toBeVisible();
}

/**
 * Assert sidebar navigation item is active
 */
export async function expectSidebarActive(page: Page, itemName: string): Promise<void> {
  const sidebar = page.locator('[data-testid="sidebar"], .sidebar, nav');
  const activeItem = sidebar.getByRole("link", { name: itemName });
  await expect(activeItem).toHaveAttribute("aria-current", "page");
}

/**
 * Assert modal is visible
 */
export async function expectModalVisible(page: Page, title?: string): Promise<void> {
  const modal = page.locator('[role="dialog"], .modal');
  await expect(modal).toBeVisible();

  if (title) {
    await expect(modal.getByRole("heading", { name: title })).toBeVisible();
  }
}

/**
 * Assert modal is not visible
 */
export async function expectModalHidden(page: Page): Promise<void> {
  const modal = page.locator('[role="dialog"], .modal');
  await expect(modal).not.toBeVisible();
}

/**
 * Assert button is enabled
 */
export async function expectButtonEnabled(
  page: Page,
  buttonName: string
): Promise<void> {
  const button = page.getByRole("button", { name: buttonName });
  await expect(button).toBeEnabled();
}

/**
 * Assert button is disabled
 */
export async function expectButtonDisabled(
  page: Page,
  buttonName: string
): Promise<void> {
  const button = page.getByRole("button", { name: buttonName });
  await expect(button).toBeDisabled();
}

/**
 * Assert notification/toast is visible
 */
export async function expectToastVisible(
  page: Page,
  message?: string
): Promise<void> {
  const toast = page.locator('[role="alert"], .toast, [data-testid="toast"]');
  await expect(toast.first()).toBeVisible();

  if (message) {
    await expect(toast.filter({ hasText: message })).toBeVisible();
  }
}

/**
 * Assert dropdown menu is open
 */
export async function expectDropdownOpen(page: Page): Promise<void> {
  const dropdown = page.locator('[role="menu"], .dropdown-menu');
  await expect(dropdown).toBeVisible();
}

/**
 * Assert input has specific value
 */
export async function expectInputValue(
  page: Page,
  label: string,
  value: string
): Promise<void> {
  const input = page.getByLabel(label);
  await expect(input).toHaveValue(value);
}

/**
 * Assert element count
 */
export async function expectElementCount(
  locator: Locator,
  count: number
): Promise<void> {
  await expect(locator).toHaveCount(count);
}

/**
 * Assert page is accessible (basic checks)
 */
export async function expectAccessible(page: Page): Promise<void> {
  // Check for main landmark
  await expect(page.locator("main, [role='main']")).toBeVisible();

  // Check for skip link or main content link
  const skipLink = page.locator('a[href="#main-content"], a[href="#content"]');
  const hasSkipLink = await skipLink.count() > 0;

  // Check images have alt text
  const images = page.locator("img");
  const imageCount = await images.count();

  for (let i = 0; i < imageCount; i++) {
    const img = images.nth(i);
    const alt = await img.getAttribute("alt");
    const role = await img.getAttribute("role");

    // Image should have alt text or role="presentation"
    if (role !== "presentation" && role !== "none") {
      expect(alt).not.toBeNull();
    }
  }
}
