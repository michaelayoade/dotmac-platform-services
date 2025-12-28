import { Page, Locator } from "@playwright/test";
import { BasePage } from "../base.page";

/**
 * Users List Page Object
 */
export class UsersPage extends BasePage {
  readonly path = "/users";

  // Page elements
  readonly createButton: Locator;
  readonly searchInput: Locator;
  readonly usersTable: Locator;
  readonly filterDropdown: Locator;

  // Table columns
  readonly nameColumn: Locator;
  readonly emailColumn: Locator;
  readonly roleColumn: Locator;
  readonly statusColumn: Locator;

  // Pagination
  readonly pagination: Locator;
  readonly nextPageButton: Locator;
  readonly prevPageButton: Locator;

  constructor(page: Page) {
    super(page);

    this.createButton = page.getByRole("link", { name: /create|new|add/i });
    this.searchInput = page.getByPlaceholder(/search/i);
    this.usersTable = page.locator("table");
    this.filterDropdown = page.locator('[data-testid="filter"], .filter-dropdown');

    this.nameColumn = page.locator('th:has-text("Name")');
    this.emailColumn = page.locator('th:has-text("Email")');
    this.roleColumn = page.locator('th:has-text("Role")');
    this.statusColumn = page.locator('th:has-text("Status")');

    this.pagination = page.locator('[data-testid="pagination"], .pagination');
    this.nextPageButton = page.getByRole("button", { name: /next/i });
    this.prevPageButton = page.getByRole("button", { name: /prev/i });
  }

  /**
   * Create a new user
   */
  async goToCreateUser(): Promise<void> {
    await this.createButton.click();
    await this.page.waitForURL("**/users/new");
  }

  /**
   * Search for users
   */
  async searchUsers(query: string): Promise<void> {
    await this.searchInput.fill(query);
    await this.page.keyboard.press("Enter");
    await this.waitForPageLoad();
  }

  /**
   * Clear search
   */
  async clearSearch(): Promise<void> {
    await this.searchInput.clear();
    await this.waitForPageLoad();
  }

  /**
   * Get user row by email
   */
  getUserRowByEmail(email: string): Locator {
    return this.usersTable.locator("tbody tr", { hasText: email });
  }

  /**
   * Open user details
   */
  async openUserDetails(email: string): Promise<void> {
    await this.getUserRowByEmail(email).click();
    await this.waitForPageLoad();
  }

  /**
   * Delete user
   */
  async deleteUser(email: string): Promise<void> {
    const row = this.getUserRowByEmail(email);
    await row.getByRole("button", { name: /delete|remove/i }).click();
    await this.confirmModal();
    await this.waitForPageLoad();
  }

  /**
   * Get total user count from table
   */
  async getUserCount(): Promise<number> {
    return await this.usersTable.locator("tbody tr").count();
  }

  /**
   * Go to next page
   */
  async nextPage(): Promise<void> {
    await this.nextPageButton.click();
    await this.waitForPageLoad();
  }

  /**
   * Go to previous page
   */
  async prevPage(): Promise<void> {
    await this.prevPageButton.click();
    await this.waitForPageLoad();
  }
}

/**
 * Create/Edit User Page Object
 */
export class UserFormPage extends BasePage {
  readonly path = "/users/new";

  // Form fields
  readonly nameInput: Locator;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly roleSelect: Locator;
  readonly statusToggle: Locator;

  // Actions
  readonly saveButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    super(page);

    this.nameInput = page.getByLabel(/name/i);
    this.emailInput = page.getByLabel(/email/i);
    this.passwordInput = page.getByLabel(/password/i);
    this.roleSelect = page.getByLabel(/role/i);
    this.statusToggle = page.getByLabel(/active|status/i);

    this.saveButton = page.getByRole("button", { name: /save|create|submit/i });
    this.cancelButton = page.getByRole("button", { name: /cancel/i });
  }

  /**
   * Fill user form
   */
  async fillUserForm(data: {
    name: string;
    email: string;
    password?: string;
    role?: string;
  }): Promise<void> {
    await this.nameInput.fill(data.name);
    await this.emailInput.fill(data.email);
    if (data.password) {
      await this.passwordInput.fill(data.password);
    }
    if (data.role) {
      await this.roleSelect.selectOption(data.role);
    }
  }

  /**
   * Save user
   */
  async save(): Promise<void> {
    await this.saveButton.click();
    await this.waitForPageLoad();
  }

  /**
   * Cancel and go back
   */
  async cancel(): Promise<void> {
    await this.cancelButton.click();
    await this.waitForPageLoad();
  }

  /**
   * Create user with all fields
   */
  async createUser(data: {
    name: string;
    email: string;
    password: string;
    role?: string;
  }): Promise<void> {
    await this.fillUserForm(data);
    await this.save();
  }
}
