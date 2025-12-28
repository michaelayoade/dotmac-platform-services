import { Page, Locator } from "@playwright/test";
import { BasePage } from "../base.page";

/**
 * Billing Dashboard Page Object
 */
export class BillingPage extends BasePage {
  readonly path = "/billing";

  // KPI Cards
  readonly monthlyRevenueCard: Locator;
  readonly annualRevenueCard: Locator;
  readonly outstandingCard: Locator;
  readonly collectionsCard: Locator;

  // Actions
  readonly createInvoiceButton: Locator;
  readonly exportReportButton: Locator;

  // Recent Items
  readonly recentInvoicesTable: Locator;
  readonly viewAllInvoicesLink: Locator;

  // Charts
  readonly revenueTrendChart: Locator;
  readonly paymentMethodsChart: Locator;

  // Navigation
  readonly invoicesLink: Locator;
  readonly subscriptionsLink: Locator;
  readonly paymentsLink: Locator;
  readonly pricingLink: Locator;

  constructor(page: Page) {
    super(page);

    // KPIs
    this.monthlyRevenueCard = page.locator('[data-testid="mrr-card"]').or(
      page.locator('.card', { hasText: /monthly revenue/i })
    );
    this.annualRevenueCard = page.locator('[data-testid="arr-card"]').or(
      page.locator('.card', { hasText: /annual revenue/i })
    );
    this.outstandingCard = page.locator('[data-testid="outstanding-card"]').or(
      page.locator('.card', { hasText: /outstanding/i })
    );
    this.collectionsCard = page.locator('[data-testid="collections-card"]').or(
      page.locator('.card', { hasText: /collections/i })
    );

    // Actions
    this.createInvoiceButton = page.getByRole("link", { name: /create invoice/i });
    this.exportReportButton = page.getByRole("button", { name: /export/i });

    // Tables
    this.recentInvoicesTable = page.locator("table");
    this.viewAllInvoicesLink = page.getByRole("link", { name: /view all/i });

    // Charts
    this.revenueTrendChart = page.locator('[data-testid="revenue-chart"]');
    this.paymentMethodsChart = page.locator('[data-testid="payment-methods-chart"]');

    // Navigation
    this.invoicesLink = page.getByRole("link", { name: /invoices/i }).first();
    this.subscriptionsLink = page.getByRole("link", { name: /subscriptions/i });
    this.paymentsLink = page.getByRole("link", { name: /payments/i });
    this.pricingLink = page.getByRole("link", { name: /pricing/i });
  }

  /**
   * Get MRR value
   */
  async getMRR(): Promise<string | null> {
    return await this.monthlyRevenueCard.locator(".text-3xl, .value").textContent();
  }

  /**
   * Get ARR value
   */
  async getARR(): Promise<string | null> {
    return await this.annualRevenueCard.locator(".text-3xl, .value").textContent();
  }

  /**
   * Navigate to create invoice
   */
  async goToCreateInvoice(): Promise<void> {
    await this.createInvoiceButton.click();
    await this.page.waitForURL("**/billing/invoices/new");
  }

  /**
   * Navigate to invoices list
   */
  async goToInvoices(): Promise<void> {
    if (await this.viewAllInvoicesLink.isVisible()) {
      await this.viewAllInvoicesLink.click();
    } else {
      await this.invoicesLink.click();
    }
    await this.waitForPageLoad();
  }

  /**
   * Navigate to subscriptions
   */
  async goToSubscriptions(): Promise<void> {
    await this.subscriptionsLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Navigate to payments
   */
  async goToPayments(): Promise<void> {
    await this.paymentsLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Export billing report
   */
  async exportReport(): Promise<void> {
    await this.exportReportButton.click();
  }
}

/**
 * Invoices List Page Object
 */
export class InvoicesPage extends BasePage {
  readonly path = "/billing/invoices";

  // Actions
  readonly createButton: Locator;
  readonly exportButton: Locator;

  // Filters
  readonly searchInput: Locator;
  readonly statusFilter: Locator;
  readonly dateRangeFilter: Locator;

  // Table
  readonly invoicesTable: Locator;

  // Pagination
  readonly pagination: Locator;

  constructor(page: Page) {
    super(page);

    this.createButton = page.getByRole("link", { name: /create|new/i }).first();
    this.exportButton = page.getByRole("button", { name: /export/i });

    this.searchInput = page.getByPlaceholder(/search/i);
    this.statusFilter = page.locator('[data-testid="status-filter"]');
    this.dateRangeFilter = page.locator('[data-testid="date-filter"]');

    this.invoicesTable = page.locator("table");
    this.pagination = page.locator('[data-testid="pagination"], .pagination');
  }

  /**
   * Navigate to create invoice
   */
  async goToCreateInvoice(): Promise<void> {
    await this.createButton.click();
    await this.page.waitForURL("**/billing/invoices/new");
  }

  /**
   * Search invoices
   */
  async searchInvoices(query: string): Promise<void> {
    await this.searchInput.fill(query);
    await this.page.keyboard.press("Enter");
    await this.waitForPageLoad();
  }

  /**
   * Filter by status
   */
  async filterByStatus(status: string): Promise<void> {
    await this.statusFilter.click();
    await this.page.getByRole("option", { name: status }).click();
    await this.waitForPageLoad();
  }

  /**
   * Get invoice row by number
   */
  getInvoiceRowByNumber(number: string): Locator {
    return this.invoicesTable.locator("tbody tr", { hasText: number });
  }

  /**
   * Open invoice details
   */
  async openInvoiceDetails(invoiceNumber: string): Promise<void> {
    await this.getInvoiceRowByNumber(invoiceNumber).click();
    await this.waitForPageLoad();
  }

  /**
   * Get invoice count
   */
  async getInvoiceCount(): Promise<number> {
    return await this.invoicesTable.locator("tbody tr").count();
  }
}

/**
 * Create Invoice Page Object
 */
export class CreateInvoicePage extends BasePage {
  readonly path = "/billing/invoices/new";

  // Form fields
  readonly customerSelect: Locator;
  readonly dueDateInput: Locator;
  readonly itemsSection: Locator;
  readonly addItemButton: Locator;
  readonly notesInput: Locator;

  // Line item fields
  readonly itemDescriptionInput: Locator;
  readonly itemQuantityInput: Locator;
  readonly itemPriceInput: Locator;

  // Totals
  readonly subtotal: Locator;
  readonly tax: Locator;
  readonly total: Locator;

  // Actions
  readonly saveDraftButton: Locator;
  readonly sendInvoiceButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    super(page);

    this.customerSelect = page.getByLabel(/customer|tenant/i);
    this.dueDateInput = page.getByLabel(/due date/i);
    this.itemsSection = page.locator('[data-testid="invoice-items"]');
    this.addItemButton = page.getByRole("button", { name: /add item|add line/i });
    this.notesInput = page.getByLabel(/notes/i);

    this.itemDescriptionInput = page.locator('[data-testid="item-description"]').first();
    this.itemQuantityInput = page.locator('[data-testid="item-quantity"]').first();
    this.itemPriceInput = page.locator('[data-testid="item-price"]').first();

    this.subtotal = page.locator('[data-testid="subtotal"]');
    this.tax = page.locator('[data-testid="tax"]');
    this.total = page.locator('[data-testid="total"]');

    this.saveDraftButton = page.getByRole("button", { name: /save draft/i });
    this.sendInvoiceButton = page.getByRole("button", { name: /send|create/i });
    this.cancelButton = page.getByRole("button", { name: /cancel/i });
  }

  /**
   * Add a line item
   */
  async addLineItem(description: string, quantity: number, price: number): Promise<void> {
    await this.addItemButton.click();
    await this.itemDescriptionInput.fill(description);
    await this.itemQuantityInput.fill(quantity.toString());
    await this.itemPriceInput.fill(price.toString());
  }

  /**
   * Create and send invoice
   */
  async createAndSendInvoice(data: {
    customer: string;
    dueDate?: string;
    items: Array<{ description: string; quantity: number; price: number }>;
    notes?: string;
  }): Promise<void> {
    await this.customerSelect.selectOption(data.customer);

    if (data.dueDate) {
      await this.dueDateInput.fill(data.dueDate);
    }

    for (const item of data.items) {
      await this.addLineItem(item.description, item.quantity, item.price);
    }

    if (data.notes) {
      await this.notesInput.fill(data.notes);
    }

    await this.sendInvoiceButton.click();
    await this.waitForPageLoad();
  }

  /**
   * Save as draft
   */
  async saveAsDraft(): Promise<void> {
    await this.saveDraftButton.click();
    await this.waitForPageLoad();
  }
}

/**
 * Subscriptions Page Object
 */
export class SubscriptionsPage extends BasePage {
  readonly path = "/billing/subscriptions";

  // Actions
  readonly createButton: Locator;

  // Filters
  readonly searchInput: Locator;
  readonly statusFilter: Locator;

  // Table
  readonly subscriptionsTable: Locator;

  constructor(page: Page) {
    super(page);

    this.createButton = page.getByRole("link", { name: /create|new/i });
    this.searchInput = page.getByPlaceholder(/search/i);
    this.statusFilter = page.locator('[data-testid="status-filter"]');
    this.subscriptionsTable = page.locator("table");
  }

  /**
   * Search subscriptions
   */
  async searchSubscriptions(query: string): Promise<void> {
    await this.searchInput.fill(query);
    await this.page.keyboard.press("Enter");
    await this.waitForPageLoad();
  }

  /**
   * Filter by status
   */
  async filterByStatus(status: string): Promise<void> {
    await this.statusFilter.click();
    await this.page.getByRole("option", { name: status }).click();
    await this.waitForPageLoad();
  }

  /**
   * Get subscription count
   */
  async getSubscriptionCount(): Promise<number> {
    return await this.subscriptionsTable.locator("tbody tr").count();
  }

  /**
   * Open subscription details
   */
  async openSubscriptionDetails(customerName: string): Promise<void> {
    await this.subscriptionsTable.locator("tbody tr", { hasText: customerName }).click();
    await this.waitForPageLoad();
  }
}
