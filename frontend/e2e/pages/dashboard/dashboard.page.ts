import { Page, Locator } from "@playwright/test";
import { BasePage } from "../base.page";

/**
 * Main Dashboard Page Object
 */
export class DashboardPage extends BasePage {
  readonly path = "/";

  // Dashboard widgets
  readonly recentActivityFeed: Locator;
  readonly systemHealthWidget: Locator;
  readonly quickActions: Locator;

  // Stats cards
  readonly statsCards: Locator;
  readonly usersCard: Locator;
  readonly tenantsCard: Locator;
  readonly revenueCard: Locator;

  // Navigation shortcuts
  readonly billingLink: Locator;
  readonly usersLink: Locator;
  readonly tenantsLink: Locator;
  readonly settingsLink: Locator;

  constructor(page: Page) {
    super(page);

    // Widgets
    this.recentActivityFeed = page.locator('[data-testid="recent-activity"], .activity-feed');
    this.systemHealthWidget = page.locator('[data-testid="system-health"], .health-widget');
    this.quickActions = page.locator('[data-testid="quick-actions"], .quick-actions');

    // Stats
    this.statsCards = page.locator('[data-testid="stats-card"], .stats-card');
    this.usersCard = page.locator('[data-testid="users-stat"]');
    this.tenantsCard = page.locator('[data-testid="tenants-stat"]');
    this.revenueCard = page.locator('[data-testid="revenue-stat"]');

    // Navigation
    this.billingLink = page.getByRole("link", { name: /billing/i }).first();
    this.usersLink = page.getByRole("link", { name: /users/i }).first();
    this.tenantsLink = page.getByRole("link", { name: /tenants/i }).first();
    this.settingsLink = page.getByRole("link", { name: /settings/i }).first();
  }

  /**
   * Get system health status
   */
  async getSystemHealthStatus(): Promise<string | null> {
    return await this.systemHealthWidget.locator(".status-badge, .health-status").textContent();
  }

  /**
   * Get recent activity count
   */
  async getRecentActivityCount(): Promise<number> {
    return await this.recentActivityFeed.locator(".activity-item, li").count();
  }

  /**
   * Click a quick action by name
   */
  async clickQuickAction(actionName: string): Promise<void> {
    await this.quickActions.getByRole("button", { name: actionName }).click();
  }

  /**
   * Navigate to billing
   */
  async goToBilling(): Promise<void> {
    await this.billingLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Navigate to users
   */
  async goToUsers(): Promise<void> {
    await this.usersLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Navigate to tenants
   */
  async goToTenants(): Promise<void> {
    await this.tenantsLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Navigate to settings
   */
  async goToSettings(): Promise<void> {
    await this.settingsLink.click();
    await this.waitForPageLoad();
  }
}

/**
 * Analytics Page Object
 */
export class AnalyticsPage extends BasePage {
  readonly path = "/analytics";

  // Charts
  readonly revenueChart: Locator;
  readonly usersChart: Locator;
  readonly conversionChart: Locator;

  // Date filters
  readonly dateRangeSelector: Locator;
  readonly last7DaysOption: Locator;
  readonly last30DaysOption: Locator;
  readonly customRangeOption: Locator;

  // Export
  readonly exportButton: Locator;

  constructor(page: Page) {
    super(page);

    this.revenueChart = page.locator('[data-testid="revenue-chart"]');
    this.usersChart = page.locator('[data-testid="users-chart"]');
    this.conversionChart = page.locator('[data-testid="conversion-chart"]');

    this.dateRangeSelector = page.locator('[data-testid="date-range"]');
    this.last7DaysOption = page.getByRole("option", { name: /7 days/i });
    this.last30DaysOption = page.getByRole("option", { name: /30 days/i });
    this.customRangeOption = page.getByRole("option", { name: /custom/i });

    this.exportButton = page.getByRole("button", { name: /export/i });
  }

  /**
   * Select date range
   */
  async selectDateRange(range: "7days" | "30days" | "custom"): Promise<void> {
    await this.dateRangeSelector.click();
    switch (range) {
      case "7days":
        await this.last7DaysOption.click();
        break;
      case "30days":
        await this.last30DaysOption.click();
        break;
      case "custom":
        await this.customRangeOption.click();
        break;
    }
    await this.waitForPageLoad();
  }

  /**
   * Export analytics data
   */
  async exportData(): Promise<void> {
    await this.exportButton.click();
  }
}
