import { Page, Locator, expect } from "@playwright/test";

/**
 * Base Page Object class with common methods and selectors
 */
export abstract class BasePage {
  protected page: Page;

  // Common selectors
  protected header: Locator;
  protected sidebar: Locator;
  protected mainContent: Locator;
  protected loadingSpinner: Locator;
  protected errorAlert: Locator;
  protected successAlert: Locator;
  protected modal: Locator;
  protected toast: Locator;

  constructor(page: Page) {
    this.page = page;
    this.header = page.locator("header");
    this.sidebar = page.locator('[data-testid="sidebar"], .sidebar, aside nav');
    this.mainContent = page.locator("#main-content, main");
    this.loadingSpinner = page.locator(
      '[data-testid="loading"], .animate-pulse, .loading-skeleton'
    );
    this.errorAlert = page.locator(
      '[role="alert"].status-error, .bg-status-error/15, [data-testid="error"]'
    );
    this.successAlert = page.locator(
      '[role="alert"].status-success, .bg-status-success, [data-testid="success"]'
    );
    this.modal = page.locator('[role="dialog"], .modal');
    this.toast = page.locator('[role="alert"], .toast, [data-testid="toast"]');
  }

  /**
   * The path for this page (to be implemented by subclasses)
   */
  abstract readonly path: string;

  /**
   * Navigate to this page
   */
  async navigate(): Promise<void> {
    await this.page.goto(this.path);
    await this.waitForPageLoad();
  }

  /**
   * Wait for page to fully load
   */
  async waitForPageLoad(): Promise<void> {
    await this.page.waitForLoadState("networkidle");
    // Wait for any loading spinners to disappear
    await this.loadingSpinner
      .waitFor({ state: "hidden", timeout: 10000 })
      .catch(() => {});
  }

  /**
   * Get the page title
   */
  async getPageTitle(): Promise<string> {
    return await this.page.title();
  }

  /**
   * Check if the page has an error displayed
   */
  async hasError(): Promise<boolean> {
    return await this.errorAlert.isVisible();
  }

  /**
   * Get the error message text
   */
  async getErrorMessage(): Promise<string | null> {
    if (await this.hasError()) {
      return await this.errorAlert.textContent();
    }
    return null;
  }

  /**
   * Check if the page has a success message
   */
  async hasSuccess(): Promise<boolean> {
    return await this.successAlert.isVisible();
  }

  /**
   * Click a button by text
   */
  async clickButton(text: string): Promise<void> {
    await this.page.getByRole("button", { name: text }).click();
  }

  /**
   * Click a link by text
   */
  async clickLink(text: string): Promise<void> {
    await this.page.getByRole("link", { name: text }).click();
  }

  /**
   * Fill an input by label
   */
  async fillInput(label: string, value: string): Promise<void> {
    await this.page.getByLabel(label).fill(value);
  }

  /**
   * Fill an input by placeholder
   */
  async fillByPlaceholder(placeholder: string, value: string): Promise<void> {
    await this.page.getByPlaceholder(placeholder).fill(value);
  }

  /**
   * Select an option from a dropdown by label
   */
  async selectOption(label: string, value: string): Promise<void> {
    await this.page.getByLabel(label).selectOption(value);
  }

  /**
   * Check a checkbox by label
   */
  async checkCheckbox(label: string): Promise<void> {
    await this.page.getByLabel(label).check();
  }

  /**
   * Uncheck a checkbox by label
   */
  async uncheckCheckbox(label: string): Promise<void> {
    await this.page.getByLabel(label).uncheck();
  }

  /**
   * Get table row count
   */
  async getTableRowCount(): Promise<number> {
    return await this.page.locator("table tbody tr").count();
  }

  /**
   * Get a table row by text content
   */
  getTableRowByText(text: string): Locator {
    return this.page.locator("table tbody tr", { hasText: text });
  }

  /**
   * Click a row action button
   */
  async clickRowAction(rowText: string, actionLabel: string): Promise<void> {
    const row = this.getTableRowByText(rowText);
    await row.getByRole("button", { name: actionLabel }).click();
  }

  /**
   * Open a row's dropdown menu
   */
  async openRowMenu(rowText: string): Promise<void> {
    const row = this.getTableRowByText(rowText);
    await row.getByRole("button", { name: /more|actions|menu/i }).click();
  }

  /**
   * Get page heading
   */
  getPageHeading(): Locator {
    return this.page.getByRole("heading", { level: 1 });
  }

  /**
   * Get header locator
   */
  getHeader(): Locator {
    return this.header;
  }

  /**
   * Get main content locator
   */
  getMainContent(): Locator {
    return this.mainContent;
  }

  /**
   * Check if modal is visible
   */
  async isModalVisible(): Promise<boolean> {
    return await this.modal.isVisible();
  }

  /**
   * Close modal by clicking close button
   */
  async closeModal(): Promise<void> {
    await this.modal.getByRole("button", { name: /close|cancel|×/i }).click();
    await expect(this.modal).not.toBeVisible();
  }

  /**
   * Confirm modal action
   */
  async confirmModal(): Promise<void> {
    await this.modal
      .getByRole("button", { name: /confirm|yes|ok|save|submit|delete/i })
      .click();
  }

  /**
   * Wait for toast notification
   */
  async waitForToast(): Promise<void> {
    await expect(this.toast.first()).toBeVisible();
  }

  /**
   * Get toast message text
   */
  async getToastMessage(): Promise<string | null> {
    if (await this.toast.first().isVisible()) {
      return await this.toast.first().textContent();
    }
    return null;
  }

  /**
   * Navigate using sidebar
   */
  async navigateViaSidebar(linkText: string): Promise<void> {
    await this.sidebar.getByRole("link", { name: linkText }).click();
    await this.waitForPageLoad();
  }

  /**
   * Check if current URL matches expected path
   */
  async isOnPage(path: string): Promise<boolean> {
    const url = this.page.url();
    return url.includes(path);
  }

  /**
   * Wait for URL to match pattern
   */
  async waitForUrl(pattern: string | RegExp): Promise<void> {
    await this.page.waitForURL(pattern);
  }

  /**
   * Take a screenshot for debugging
   */
  async takeScreenshot(name: string): Promise<void> {
    await this.page.screenshot({
      path: `playwright/test-results/screenshots/${name}.png`,
      fullPage: true,
    });
  }

  /**
   * Search using the search input
   */
  async search(query: string): Promise<void> {
    const searchInput = this.page.getByPlaceholder(/search/i);
    await searchInput.fill(query);
    await this.page.keyboard.press("Enter");
    await this.waitForPageLoad();
  }

  /**
   * Clear search input
   */
  async clearSearch(): Promise<void> {
    const searchInput = this.page.getByPlaceholder(/search/i);
    await searchInput.clear();
    await this.waitForPageLoad();
  }

  /**
   * Open user menu in header
   */
  async openUserMenu(): Promise<void> {
    await this.header
      .getByRole("button", { name: /user|profile|account/i })
      .click();
  }

  /**
   * Logout via user menu
   */
  async logout(): Promise<void> {
    await this.openUserMenu();
    await this.page.getByRole("menuitem", { name: /logout|sign out/i }).click();
  }

  /**
   * Get the current URL path
   */
  getCurrentPath(): string {
    const url = new URL(this.page.url());
    return url.pathname;
  }

  /**
   * Verify page is accessible (basic checks)
   */
  async verifyAccessibility(): Promise<void> {
    // Check main content exists
    await expect(this.mainContent).toBeVisible();

    // Check page has a heading
    const heading = this.page.getByRole("heading", { level: 1 });
    await expect(heading.first()).toBeVisible();
  }
}
