import { Page, Locator } from "@playwright/test";
import { BasePage } from "../base.page";

/**
 * Partner Login Page Object
 */
export class PartnerLoginPage extends BasePage {
  readonly path = "/partner/login";

  // Form elements
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly forgotPasswordLink: Locator;
  readonly applyLink: Locator;

  // Error display
  readonly errorMessage: Locator;

  constructor(page: Page) {
    super(page);

    this.emailInput = page.locator('input[type="email"], input#email, input[name="email"]');
    this.passwordInput = page.locator('input[type="password"], input#password, input[name="password"]');
    this.submitButton = page.locator('button[type="submit"]');
    this.forgotPasswordLink = page.getByRole("link", { name: /forgot password/i });
    this.applyLink = page.getByRole("link", { name: /apply|become a partner|contact us/i });

    this.errorMessage = page.locator(".status-error, .bg-status-error, [role='alert']");
  }

  /**
   * Login as partner
   */
  async login(email: string, password: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  /**
   * Navigate to partner application
   */
  async goToApply(): Promise<void> {
    await this.applyLink.click();
  }
}

/**
 * Partner Application Page Object
 */
export class PartnerApplyPage extends BasePage {
  readonly path = "/partner/apply";

  // Form fields
  readonly companyNameInput: Locator;
  readonly contactNameInput: Locator;
  readonly emailInput: Locator;
  readonly phoneInput: Locator;
  readonly websiteInput: Locator;
  readonly descriptionInput: Locator;
  readonly termsCheckbox: Locator;

  // Actions
  readonly submitButton: Locator;

  // Messages
  readonly successMessage: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    super(page);

    this.companyNameInput = page.locator('input[name="companyName"]');
    this.contactNameInput = page.locator('input[name="contactName"]');
    this.emailInput = page.locator('input[name="contactEmail"]');
    this.phoneInput = page.locator('input[name="phone"]');
    this.websiteInput = page.locator('input[name="website"]');
    this.descriptionInput = page.locator('textarea[name="businessDescription"]');
    this.termsCheckbox = page.locator('input[type="checkbox"]');

    this.submitButton = page.getByRole("button", { name: /submit|apply/i });

    this.successMessage = page.locator(".status-success, .bg-status-success");
    this.errorMessage = page.locator(".status-error, .bg-status-error, [role='alert']");
  }

  /**
   * Submit partner application
   */
  async submitApplication(data: {
    companyName: string;
    contactName: string;
    email: string;
    phone?: string;
    website?: string;
    description?: string;
  }): Promise<void> {
    await this.companyNameInput.fill(data.companyName);
    await this.contactNameInput.fill(data.contactName);
    await this.emailInput.fill(data.email);

    if (data.phone) {
      await this.phoneInput.fill(data.phone);
    }
    if (data.website) {
      await this.websiteInput.fill(data.website);
    }
    if (data.description) {
      await this.descriptionInput.fill(data.description);
    }

    await this.termsCheckbox.check();
    await this.submitButton.click();
  }
}

/**
 * Partner Dashboard Page Object
 */
export class PartnerDashboardPage extends BasePage {
  readonly path = "/partner";

  // Stats
  readonly totalReferralsCard: Locator;
  readonly pendingCommissionsCard: Locator;
  readonly totalEarningsCard: Locator;

  // Navigation
  readonly commissionsLink: Locator;
  readonly referralsLink: Locator;
  readonly statementsLink: Locator;
  readonly teamLink: Locator;
  readonly tenantsLink: Locator;
  readonly settingsLink: Locator;

  // Quick actions
  readonly newReferralButton: Locator;

  constructor(page: Page) {
    super(page);

    // Stats
    this.totalReferralsCard = page.locator('[data-testid="referrals-stat"]').or(
      page.locator('.card', { hasText: /referrals/i })
    );
    this.pendingCommissionsCard = page.locator('[data-testid="pending-commissions"]').or(
      page.locator('.card', { hasText: /pending/i })
    );
    this.totalEarningsCard = page.locator('[data-testid="earnings-stat"]').or(
      page.locator('.card', { hasText: /earnings/i })
    );

    // Navigation
    this.commissionsLink = page.getByRole("link", { name: /commissions/i });
    this.referralsLink = page.getByRole("link", { name: /referrals/i });
    this.statementsLink = page.getByRole("link", { name: /statements/i });
    this.teamLink = page.getByRole("link", { name: /team/i });
    this.tenantsLink = page.getByRole("link", { name: /tenants/i });
    this.settingsLink = page.getByRole("link", { name: /settings/i });

    // Actions
    this.newReferralButton = page.getByRole("button", { name: /new referral|add referral/i });
  }

  /**
   * Navigate to commissions
   */
  async goToCommissions(): Promise<void> {
    await this.commissionsLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Navigate to referrals
   */
  async goToReferrals(): Promise<void> {
    await this.referralsLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Navigate to statements
   */
  async goToStatements(): Promise<void> {
    await this.statementsLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Create new referral
   */
  async startNewReferral(): Promise<void> {
    await this.newReferralButton.click();
  }
}

/**
 * Partner Commissions Page Object
 */
export class PartnerCommissionsPage extends BasePage {
  readonly path = "/partner/commissions";

  // Filters
  readonly dateRangeFilter: Locator;
  readonly statusFilter: Locator;

  // Table
  readonly commissionsTable: Locator;

  // Stats
  readonly totalCommissions: Locator;
  readonly pendingCommissions: Locator;
  readonly paidCommissions: Locator;

  constructor(page: Page) {
    super(page);

    this.dateRangeFilter = page.locator('[data-testid="date-filter"]');
    this.statusFilter = page.locator('[data-testid="status-filter"]');
    this.commissionsTable = page.locator("table");

    this.totalCommissions = page.locator('[data-testid="total-commissions"]');
    this.pendingCommissions = page.locator('[data-testid="pending-commissions"]');
    this.paidCommissions = page.locator('[data-testid="paid-commissions"]');
  }

  /**
   * Get commission count
   */
  async getCommissionCount(): Promise<number> {
    return await this.commissionsTable.locator("tbody tr").count();
  }

  /**
   * Filter by status
   */
  async filterByStatus(status: string): Promise<void> {
    await this.statusFilter.click();
    await this.page.getByRole("option", { name: status }).click();
    await this.waitForPageLoad();
  }
}

/**
 * Partner Referrals Page Object
 */
export class PartnerReferralsPage extends BasePage {
  readonly path = "/partner/referrals";

  // Actions
  readonly newReferralButton: Locator;

  // Table
  readonly referralsTable: Locator;

  // Filters
  readonly statusFilter: Locator;

  constructor(page: Page) {
    super(page);

    this.newReferralButton = page.getByRole("button", { name: /new referral|add/i });
    this.referralsTable = page.locator("table");
    this.statusFilter = page.locator('[data-testid="status-filter"]');
  }

  /**
   * Create new referral
   */
  async createReferral(data: {
    companyName: string;
    contactName: string;
    email: string;
    phone?: string;
    notes?: string;
  }): Promise<void> {
    await this.newReferralButton.click();

    // Fill referral form in modal
    await this.page.getByLabel(/company name/i).fill(data.companyName);
    await this.page.getByLabel(/contact name/i).fill(data.contactName);
    await this.page.getByLabel(/email/i).fill(data.email);

    if (data.phone) {
      await this.page.getByLabel(/phone/i).fill(data.phone);
    }
    if (data.notes) {
      await this.page.getByLabel(/notes/i).fill(data.notes);
    }

    await this.page.getByRole("button", { name: /submit|create/i }).click();
    await this.waitForPageLoad();
  }

  /**
   * Get referral count
   */
  async getReferralCount(): Promise<number> {
    return await this.referralsTable.locator("tbody tr").count();
  }
}

/**
 * Partner Statements Page Object
 */
export class PartnerStatementsPage extends BasePage {
  readonly path = "/partner/statements";

  // Table
  readonly statementsTable: Locator;

  // Filters
  readonly yearFilter: Locator;

  constructor(page: Page) {
    super(page);

    this.statementsTable = page.locator("table");
    this.yearFilter = page.locator('[data-testid="year-filter"]');
  }

  /**
   * Download statement
   */
  async downloadStatement(period: string): Promise<void> {
    const row = this.statementsTable.locator("tbody tr", { hasText: period });
    await row.getByRole("button", { name: /download/i }).click();
  }

  /**
   * Get statement count
   */
  async getStatementCount(): Promise<number> {
    return await this.statementsTable.locator("tbody tr").count();
  }
}

/**
 * Partner Team Page Object
 */
export class PartnerTeamPage extends BasePage {
  readonly path = "/partner/team";

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
}

/**
 * Partner Settings Page Object
 */
export class PartnerSettingsPage extends BasePage {
  readonly path = "/partner/settings";

  // Form fields
  readonly companyNameInput: Locator;
  readonly contactEmailInput: Locator;
  readonly paymentDetailsSection: Locator;

  // Actions
  readonly saveButton: Locator;

  constructor(page: Page) {
    super(page);

    this.companyNameInput = page.getByLabel(/company name/i);
    this.contactEmailInput = page.getByLabel(/email/i);
    this.paymentDetailsSection = page.locator('[data-testid="payment-details"]');

    this.saveButton = page.getByRole("button", { name: /save/i });
  }

  /**
   * Update company name
   */
  async updateCompanyName(name: string): Promise<void> {
    await this.companyNameInput.fill(name);
    await this.saveButton.click();
    await this.waitForPageLoad();
  }
}
