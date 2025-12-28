import { Page, Locator } from "@playwright/test";
import { BasePage } from "../base.page";

/**
 * Portal Login Page Object
 */
export class PortalLoginPage extends BasePage {
  readonly path = "/portal/login";

  // Form elements
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly forgotPasswordLink: Locator;

  // Error display
  readonly errorMessage: Locator;

  constructor(page: Page) {
    super(page);

    this.emailInput = page.locator('input[type="email"], input#email, input[name="email"]');
    this.passwordInput = page.locator('input[type="password"], input#password, input[name="password"]');
    this.submitButton = page.locator('button[type="submit"]');
    this.forgotPasswordLink = page.getByRole("link", { name: /forgot password/i });

    this.errorMessage = page.locator(".status-error, .bg-status-error, [role='alert']");
  }

  /**
   * Login to portal
   */
  async login(email: string, password: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }
}

/**
 * Portal Dashboard Page Object
 */
export class PortalDashboardPage extends BasePage {
  readonly path = "/portal";

  // Stats
  readonly currentPlanCard: Locator;
  readonly usageCard: Locator;
  readonly nextBillingCard: Locator;

  // Quick links
  readonly billingLink: Locator;
  readonly teamLink: Locator;
  readonly settingsLink: Locator;
  readonly usageLink: Locator;

  // Support
  readonly helpLink: Locator;

  constructor(page: Page) {
    super(page);

    // Stats
    this.currentPlanCard = page.locator('[data-testid="current-plan"]').or(
      page.locator('.card', { hasText: /plan/i })
    );
    this.usageCard = page.locator('[data-testid="usage-stat"]').or(
      page.locator('.card', { hasText: /usage/i })
    );
    this.nextBillingCard = page.locator('[data-testid="next-billing"]').or(
      page.locator('.card', { hasText: /billing/i })
    );

    // Links
    this.billingLink = page.getByRole("link", { name: /billing/i });
    this.teamLink = page.getByRole("link", { name: /team/i });
    this.settingsLink = page.getByRole("link", { name: /settings/i });
    this.usageLink = page.getByRole("link", { name: /usage/i });
    this.helpLink = page.getByRole("link", { name: /help|support/i });
  }

  /**
   * Navigate to billing
   */
  async goToBilling(): Promise<void> {
    await this.billingLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Navigate to team
   */
  async goToTeam(): Promise<void> {
    await this.teamLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Navigate to settings
   */
  async goToSettings(): Promise<void> {
    await this.settingsLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Navigate to usage
   */
  async goToUsage(): Promise<void> {
    await this.usageLink.click();
    await this.waitForPageLoad();
  }
}

/**
 * Portal Billing Page Object
 */
export class PortalBillingPage extends BasePage {
  readonly path = "/portal/billing";

  // Current plan
  readonly currentPlanSection: Locator;
  readonly planName: Locator;
  readonly planPrice: Locator;
  readonly changePlanButton: Locator;

  // Payment method
  readonly paymentMethodSection: Locator;
  readonly updatePaymentButton: Locator;

  // Invoices
  readonly invoicesSection: Locator;
  readonly invoicesTable: Locator;

  constructor(page: Page) {
    super(page);

    // Current plan
    this.currentPlanSection = page.locator('[data-testid="current-plan"]');
    this.planName = page.locator('[data-testid="plan-name"]');
    this.planPrice = page.locator('[data-testid="plan-price"]');
    this.changePlanButton = page.getByRole("button", { name: /change plan|upgrade/i });

    // Payment
    this.paymentMethodSection = page.locator('[data-testid="payment-method"]');
    this.updatePaymentButton = page.getByRole("button", { name: /update payment|change card/i });

    // Invoices
    this.invoicesSection = page.locator('[data-testid="invoices"]');
    this.invoicesTable = page.locator("table");
  }

  /**
   * Get current plan name
   */
  async getCurrentPlanName(): Promise<string | null> {
    return await this.planName.textContent();
  }

  /**
   * Open plan change modal
   */
  async openChangePlan(): Promise<void> {
    await this.changePlanButton.click();
  }

  /**
   * Open payment update modal
   */
  async openUpdatePayment(): Promise<void> {
    await this.updatePaymentButton.click();
  }

  /**
   * Download invoice
   */
  async downloadInvoice(invoiceNumber: string): Promise<void> {
    const row = this.invoicesTable.locator("tbody tr", { hasText: invoiceNumber });
    await row.getByRole("button", { name: /download/i }).click();
  }

  /**
   * Get invoice count
   */
  async getInvoiceCount(): Promise<number> {
    return await this.invoicesTable.locator("tbody tr").count();
  }
}

/**
 * Portal Settings Page Object
 */
export class PortalSettingsPage extends BasePage {
  readonly path = "/portal/settings";

  // Profile section
  readonly profileSection: Locator;
  readonly nameInput: Locator;
  readonly emailInput: Locator;

  // Organization section
  readonly organizationSection: Locator;
  readonly orgNameInput: Locator;

  // Password section
  readonly passwordSection: Locator;
  readonly currentPasswordInput: Locator;
  readonly newPasswordInput: Locator;

  // Actions
  readonly saveButton: Locator;
  readonly changePasswordButton: Locator;

  constructor(page: Page) {
    super(page);

    // Profile
    this.profileSection = page.locator('[data-testid="profile-settings"]');
    this.nameInput = page.getByLabel(/name/i);
    this.emailInput = page.getByLabel(/email/i);

    // Organization
    this.organizationSection = page.locator('[data-testid="org-settings"]');
    this.orgNameInput = page.getByLabel(/organization name/i);

    // Password
    this.passwordSection = page.locator('[data-testid="password-settings"]');
    this.currentPasswordInput = page.getByLabel(/current password/i);
    this.newPasswordInput = page.getByLabel(/new password/i);

    // Actions
    this.saveButton = page.getByRole("button", { name: /save/i });
    this.changePasswordButton = page.getByRole("button", { name: /change password/i });
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
    await this.changePasswordButton.click();
    await this.waitForPageLoad();
  }
}

/**
 * Portal Team Page Object
 */
export class PortalTeamPage extends BasePage {
  readonly path = "/portal/team";

  // Actions
  readonly inviteButton: Locator;

  // Table
  readonly teamTable: Locator;

  constructor(page: Page) {
    super(page);

    this.inviteButton = page.getByRole("button", { name: /invite|add/i });
    this.teamTable = page.locator("table");
  }

  /**
   * Invite team member
   */
  async inviteTeamMember(email: string, role?: string): Promise<void> {
    await this.inviteButton.click();
    await this.page.getByLabel(/email/i).fill(email);
    if (role) {
      await this.page.getByLabel(/role/i).selectOption(role);
    }
    await this.page.getByRole("button", { name: /invite|send/i }).click();
    await this.waitForPageLoad();
  }

  /**
   * Get team member count
   */
  async getTeamMemberCount(): Promise<number> {
    return await this.teamTable.locator("tbody tr").count();
  }

  /**
   * Remove team member
   */
  async removeTeamMember(email: string): Promise<void> {
    const row = this.teamTable.locator("tbody tr", { hasText: email });
    await row.getByRole("button", { name: /remove|delete/i }).click();
    await this.confirmModal();
    await this.waitForPageLoad();
  }
}

/**
 * Portal Usage Page Object
 */
export class PortalUsagePage extends BasePage {
  readonly path = "/portal/usage";

  // Stats
  readonly currentUsageCard: Locator;
  readonly limitCard: Locator;
  readonly usagePercentage: Locator;

  // Charts
  readonly usageChart: Locator;

  // Filters
  readonly periodFilter: Locator;

  constructor(page: Page) {
    super(page);

    this.currentUsageCard = page.locator('[data-testid="current-usage"]');
    this.limitCard = page.locator('[data-testid="usage-limit"]');
    this.usagePercentage = page.locator('[data-testid="usage-percentage"]');

    this.usageChart = page.locator('[data-testid="usage-chart"]');
    this.periodFilter = page.locator('[data-testid="period-filter"]');
  }

  /**
   * Get current usage value
   */
  async getCurrentUsage(): Promise<string | null> {
    return await this.currentUsageCard.locator(".value, .text-3xl").textContent();
  }

  /**
   * Get usage percentage
   */
  async getUsagePercentage(): Promise<string | null> {
    return await this.usagePercentage.textContent();
  }

  /**
   * Change period filter
   */
  async filterByPeriod(period: string): Promise<void> {
    await this.periodFilter.click();
    await this.page.getByRole("option", { name: period }).click();
    await this.waitForPageLoad();
  }
}
