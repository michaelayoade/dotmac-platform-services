import { Page, Locator } from "@playwright/test";
import { BasePage } from "../base.page";

/**
 * Settings Page Object
 */
export class SettingsPage extends BasePage {
  readonly path = "/settings";

  // Navigation tabs
  readonly profileTab: Locator;
  readonly organizationTab: Locator;
  readonly apiKeysTab: Locator;
  readonly securityTab: Locator;
  readonly notificationsTab: Locator;

  // Links to sub-pages
  readonly profileLink: Locator;
  readonly organizationLink: Locator;
  readonly apiKeysLink: Locator;
  readonly auditLink: Locator;
  readonly brandingLink: Locator;
  readonly featureFlagsLink: Locator;
  readonly integrationsLink: Locator;
  readonly webhooksLink: Locator;
  readonly secretsLink: Locator;
  readonly rolesLink: Locator;

  constructor(page: Page) {
    super(page);

    // Tabs
    this.profileTab = page.getByRole("tab", { name: /profile/i });
    this.organizationTab = page.getByRole("tab", { name: /organization/i });
    this.apiKeysTab = page.getByRole("tab", { name: /api keys/i });
    this.securityTab = page.getByRole("tab", { name: /security/i });
    this.notificationsTab = page.getByRole("tab", { name: /notifications/i });

    // Links
    this.profileLink = page.getByRole("link", { name: /profile/i });
    this.organizationLink = page.getByRole("link", { name: /organization/i });
    this.apiKeysLink = page.getByRole("link", { name: /api keys/i });
    this.auditLink = page.getByRole("link", { name: /audit/i });
    this.brandingLink = page.getByRole("link", { name: /branding/i });
    this.featureFlagsLink = page.getByRole("link", { name: /feature flags/i });
    this.integrationsLink = page.getByRole("link", { name: /integrations/i });
    this.webhooksLink = page.getByRole("link", { name: /webhooks/i });
    this.secretsLink = page.getByRole("link", { name: /secrets/i });
    this.rolesLink = page.getByRole("link", { name: /roles/i });
  }

  /**
   * Navigate to profile settings
   */
  async goToProfile(): Promise<void> {
    await this.profileLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Navigate to organization settings
   */
  async goToOrganization(): Promise<void> {
    await this.organizationLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Navigate to API keys
   */
  async goToApiKeys(): Promise<void> {
    await this.apiKeysLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Navigate to audit log
   */
  async goToAudit(): Promise<void> {
    await this.auditLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Navigate to webhooks
   */
  async goToWebhooks(): Promise<void> {
    await this.webhooksLink.click();
    await this.waitForPageLoad();
  }
}

/**
 * Profile Settings Page Object
 */
export class ProfileSettingsPage extends BasePage {
  readonly path = "/settings/profile";

  // Form fields
  readonly nameInput: Locator;
  readonly emailInput: Locator;
  readonly avatarUpload: Locator;
  readonly timezoneSelect: Locator;
  readonly languageSelect: Locator;

  // Password change
  readonly currentPasswordInput: Locator;
  readonly newPasswordInput: Locator;
  readonly confirmPasswordInput: Locator;
  readonly changePasswordButton: Locator;

  // Actions
  readonly saveButton: Locator;

  constructor(page: Page) {
    super(page);

    this.nameInput = page.getByLabel(/name/i);
    this.emailInput = page.getByLabel(/email/i);
    this.avatarUpload = page.locator('input[type="file"]');
    this.timezoneSelect = page.getByLabel(/timezone/i);
    this.languageSelect = page.getByLabel(/language/i);

    this.currentPasswordInput = page.getByLabel(/current password/i);
    this.newPasswordInput = page.getByLabel(/new password/i);
    this.confirmPasswordInput = page.getByLabel(/confirm password/i);
    this.changePasswordButton = page.getByRole("button", { name: /change password/i });

    this.saveButton = page.getByRole("button", { name: /save/i });
  }

  /**
   * Update profile name
   */
  async updateName(name: string): Promise<void> {
    await this.nameInput.fill(name);
    await this.saveButton.click();
    await this.waitForPageLoad();
  }

  /**
   * Change password
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await this.currentPasswordInput.fill(currentPassword);
    await this.newPasswordInput.fill(newPassword);
    await this.confirmPasswordInput.fill(newPassword);
    await this.changePasswordButton.click();
    await this.waitForPageLoad();
  }
}

/**
 * API Keys Page Object
 */
export class ApiKeysPage extends BasePage {
  readonly path = "/settings/api-keys";

  // Actions
  readonly createButton: Locator;

  // Table
  readonly apiKeysTable: Locator;

  constructor(page: Page) {
    super(page);

    this.createButton = page.getByRole("button", { name: /create|generate|new/i });
    this.apiKeysTable = page.locator("table");
  }

  /**
   * Create new API key
   */
  async createApiKey(name: string): Promise<void> {
    await this.createButton.click();
    await this.page.getByLabel(/name/i).fill(name);
    await this.page.getByRole("button", { name: /create|generate/i }).click();
    await this.waitForPageLoad();
  }

  /**
   * Revoke API key
   */
  async revokeApiKey(keyName: string): Promise<void> {
    const row = this.apiKeysTable.locator("tbody tr", { hasText: keyName });
    await row.getByRole("button", { name: /revoke|delete/i }).click();
    await this.confirmModal();
    await this.waitForPageLoad();
  }

  /**
   * Get API key count
   */
  async getApiKeyCount(): Promise<number> {
    return await this.apiKeysTable.locator("tbody tr").count();
  }
}

/**
 * Webhooks Page Object
 */
export class WebhooksPage extends BasePage {
  readonly path = "/settings/webhooks";

  // Actions
  readonly createButton: Locator;

  // Table
  readonly webhooksTable: Locator;

  constructor(page: Page) {
    super(page);

    this.createButton = page.getByRole("link", { name: /create|new|add/i });
    this.webhooksTable = page.locator("table");
  }

  /**
   * Navigate to create webhook
   */
  async goToCreateWebhook(): Promise<void> {
    await this.createButton.click();
    await this.page.waitForURL("**/settings/webhooks/new");
  }

  /**
   * Get webhook count
   */
  async getWebhookCount(): Promise<number> {
    return await this.webhooksTable.locator("tbody tr").count();
  }

  /**
   * Open webhook details
   */
  async openWebhookDetails(url: string): Promise<void> {
    await this.webhooksTable.locator("tbody tr", { hasText: url }).click();
    await this.waitForPageLoad();
  }
}
