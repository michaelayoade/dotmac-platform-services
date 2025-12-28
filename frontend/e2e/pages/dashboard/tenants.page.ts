import { Page, Locator } from "@playwright/test";
import { BasePage } from "../base.page";

/**
 * Tenants List Page Object
 */
export class TenantsPage extends BasePage {
  readonly path = "/tenants";

  // Page elements
  readonly createButton: Locator;
  readonly searchInput: Locator;
  readonly tenantsTable: Locator;
  readonly filterDropdown: Locator;

  // Stats
  readonly totalTenantsCount: Locator;
  readonly activeTenantsCount: Locator;

  // Pagination
  readonly pagination: Locator;

  constructor(page: Page) {
    super(page);

    this.createButton = page.getByRole("link", { name: /create|new|add/i });
    this.searchInput = page.getByPlaceholder(/search/i);
    this.tenantsTable = page.locator("table");
    this.filterDropdown = page.locator('[data-testid="filter"], .filter-dropdown');

    this.totalTenantsCount = page.locator('[data-testid="total-count"]');
    this.activeTenantsCount = page.locator('[data-testid="active-count"]');

    this.pagination = page.locator('[data-testid="pagination"], .pagination');
  }

  /**
   * Navigate to create tenant
   */
  async goToCreateTenant(): Promise<void> {
    await this.createButton.click();
    await this.page.waitForURL("**/tenants/new");
  }

  /**
   * Search tenants
   */
  async searchTenants(query: string): Promise<void> {
    await this.searchInput.fill(query);
    await this.page.keyboard.press("Enter");
    await this.waitForPageLoad();
  }

  /**
   * Get tenant row by name
   */
  getTenantRowByName(name: string): Locator {
    return this.tenantsTable.locator("tbody tr", { hasText: name });
  }

  /**
   * Open tenant details
   */
  async openTenantDetails(name: string): Promise<void> {
    await this.getTenantRowByName(name).click();
    await this.waitForPageLoad();
  }

  /**
   * Get tenant count
   */
  async getTenantCount(): Promise<number> {
    return await this.tenantsTable.locator("tbody tr").count();
  }

  /**
   * Delete tenant
   */
  async deleteTenant(name: string): Promise<void> {
    const row = this.getTenantRowByName(name);
    await row.getByRole("button", { name: /delete|remove/i }).click();
    await this.confirmModal();
    await this.waitForPageLoad();
  }
}

/**
 * Tenant Details Page Object
 */
export class TenantDetailsPage extends BasePage {
  readonly path = "/tenants/[id]";

  // Sections
  readonly overviewSection: Locator;
  readonly usersSection: Locator;
  readonly billingSection: Locator;
  readonly settingsSection: Locator;

  // Tabs
  readonly overviewTab: Locator;
  readonly usersTab: Locator;
  readonly billingTab: Locator;
  readonly settingsTab: Locator;

  // Actions
  readonly editButton: Locator;
  readonly deleteButton: Locator;
  readonly suspendButton: Locator;

  // Info
  readonly tenantName: Locator;
  readonly tenantDomain: Locator;
  readonly tenantStatus: Locator;
  readonly tenantPlan: Locator;

  constructor(page: Page) {
    super(page);

    // Sections
    this.overviewSection = page.locator('[data-testid="overview"]');
    this.usersSection = page.locator('[data-testid="users"]');
    this.billingSection = page.locator('[data-testid="billing"]');
    this.settingsSection = page.locator('[data-testid="settings"]');

    // Tabs
    this.overviewTab = page.getByRole("tab", { name: /overview/i });
    this.usersTab = page.getByRole("tab", { name: /users/i });
    this.billingTab = page.getByRole("tab", { name: /billing/i });
    this.settingsTab = page.getByRole("tab", { name: /settings/i });

    // Actions
    this.editButton = page.getByRole("button", { name: /edit/i });
    this.deleteButton = page.getByRole("button", { name: /delete/i });
    this.suspendButton = page.getByRole("button", { name: /suspend/i });

    // Info
    this.tenantName = page.locator('[data-testid="tenant-name"], h1');
    this.tenantDomain = page.locator('[data-testid="tenant-domain"]');
    this.tenantStatus = page.locator('[data-testid="tenant-status"], .status-badge');
    this.tenantPlan = page.locator('[data-testid="tenant-plan"]');
  }

  /**
   * Navigate by ID
   */
  async navigateToTenant(id: string): Promise<void> {
    await this.page.goto(`/tenants/${id}`);
    await this.waitForPageLoad();
  }

  /**
   * Get tenant name
   */
  async getTenantName(): Promise<string | null> {
    return await this.tenantName.textContent();
  }

  /**
   * Switch to tab
   */
  async switchTab(tab: "overview" | "users" | "billing" | "settings"): Promise<void> {
    const tabLocators = {
      overview: this.overviewTab,
      users: this.usersTab,
      billing: this.billingTab,
      settings: this.settingsTab,
    };
    await tabLocators[tab].click();
    await this.waitForPageLoad();
  }

  /**
   * Edit tenant
   */
  async edit(): Promise<void> {
    await this.editButton.click();
    await this.waitForPageLoad();
  }

  /**
   * Delete tenant
   */
  async delete(): Promise<void> {
    await this.deleteButton.click();
    await this.confirmModal();
  }

  /**
   * Suspend tenant
   */
  async suspend(): Promise<void> {
    await this.suspendButton.click();
    await this.confirmModal();
  }
}

/**
 * Create Tenant Page Object
 */
export class CreateTenantPage extends BasePage {
  readonly path = "/tenants/new";

  // Form fields
  readonly nameInput: Locator;
  readonly domainInput: Locator;
  readonly planSelect: Locator;
  readonly adminEmailInput: Locator;
  readonly adminNameInput: Locator;

  // Actions
  readonly createButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    super(page);

    this.nameInput = page.getByLabel(/name/i);
    this.domainInput = page.getByLabel(/domain/i);
    this.planSelect = page.getByLabel(/plan/i);
    this.adminEmailInput = page.getByLabel(/admin email/i);
    this.adminNameInput = page.getByLabel(/admin name/i);

    this.createButton = page.getByRole("button", { name: /create|save|submit/i });
    this.cancelButton = page.getByRole("button", { name: /cancel/i });
  }

  /**
   * Fill tenant form
   */
  async fillTenantForm(data: {
    name: string;
    domain?: string;
    plan?: string;
    adminEmail?: string;
    adminName?: string;
  }): Promise<void> {
    await this.nameInput.fill(data.name);
    if (data.domain) {
      await this.domainInput.fill(data.domain);
    }
    if (data.plan) {
      await this.planSelect.selectOption(data.plan);
    }
    if (data.adminEmail) {
      await this.adminEmailInput.fill(data.adminEmail);
    }
    if (data.adminName) {
      await this.adminNameInput.fill(data.adminName);
    }
  }

  /**
   * Create tenant
   */
  async createTenant(data: {
    name: string;
    domain?: string;
    plan?: string;
    adminEmail?: string;
    adminName?: string;
  }): Promise<void> {
    await this.fillTenantForm(data);
    await this.createButton.click();
    await this.waitForPageLoad();
  }

  /**
   * Cancel creation
   */
  async cancel(): Promise<void> {
    await this.cancelButton.click();
    await this.waitForPageLoad();
  }
}
