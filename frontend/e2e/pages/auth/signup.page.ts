import { Page, Locator } from "@playwright/test";
import { BasePage } from "../base.page";

/**
 * Signup Page Object
 */
export class SignupPage extends BasePage {
  readonly path = "/signup";

  // Form elements
  readonly nameInput: Locator;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly confirmPasswordInput: Locator;
  readonly termsCheckbox: Locator;
  readonly submitButton: Locator;
  readonly loginLink: Locator;

  // Organization step (if multi-step)
  readonly organizationNameInput: Locator;

  // Plan selection step
  readonly planCards: Locator;

  // Error display
  readonly errorMessage: Locator;

  // Progress indicator
  readonly progressSteps: Locator;

  constructor(page: Page) {
    super(page);

    // Form elements
    this.nameInput = page.locator('input[name="name"], input#name');
    this.emailInput = page.locator('input[type="email"], input#email, input[name="email"]');
    this.passwordInput = page.locator('input#password, input[name="password"]').first();
    this.confirmPasswordInput = page.locator('input#confirmPassword, input[name="confirmPassword"]');
    this.termsCheckbox = page.locator('input#terms, input[name="terms"]');
    this.submitButton = page.locator('button[type="submit"]');
    this.loginLink = page.getByRole("link", { name: /sign in|log in/i });

    // Organization step
    this.organizationNameInput = page.locator('input[name="organizationName"], input#organizationName');

    // Plan selection
    this.planCards = page.locator('[data-testid="plan-card"], .plan-card');

    // Error display
    this.errorMessage = page.locator(".status-error, .bg-status-error, [role='alert']");

    // Progress
    this.progressSteps = page.locator('[data-testid="step"], .step-indicator');
  }

  /**
   * Fill account information (step 1)
   */
  async fillAccountInfo(name: string, email: string, password: string): Promise<void> {
    await this.nameInput.fill(name);
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    if (await this.confirmPasswordInput.isVisible()) {
      await this.confirmPasswordInput.fill(password);
    }
  }

  /**
   * Fill organization information (step 2)
   */
  async fillOrganizationInfo(organizationName: string): Promise<void> {
    await this.organizationNameInput.fill(organizationName);
  }

  /**
   * Select a plan
   */
  async selectPlan(planName: string): Promise<void> {
    await this.planCards.filter({ hasText: planName }).click();
  }

  /**
   * Accept terms and conditions
   */
  async acceptTerms(): Promise<void> {
    await this.termsCheckbox.check();
  }

  /**
   * Submit current step
   */
  async submitStep(): Promise<void> {
    await this.submitButton.click();
  }

  /**
   * Complete full signup flow
   */
  async completeSignup(
    name: string,
    email: string,
    password: string,
    organizationName?: string,
    planName?: string
  ): Promise<void> {
    // Step 1: Account info
    await this.fillAccountInfo(name, email, password);
    await this.submitStep();

    // Step 2: Organization (if visible)
    if (organizationName && (await this.organizationNameInput.isVisible())) {
      await this.fillOrganizationInfo(organizationName);
      await this.submitStep();
    }

    // Step 3: Plan selection (if visible)
    if (planName && (await this.planCards.first().isVisible())) {
      await this.selectPlan(planName);
      await this.submitStep();
    }

    // Accept terms if visible
    if (await this.termsCheckbox.isVisible()) {
      await this.acceptTerms();
      await this.submitStep();
    }
  }

  /**
   * Get current step number
   */
  async getCurrentStep(): Promise<number> {
    const count = await this.progressSteps.count();
    for (let i = 0; i < count; i++) {
      const step = this.progressSteps.nth(i);
      if (await step.evaluate((el) => el.classList.contains("active"))) {
        return i + 1;
      }
    }
    return 1;
  }

  /**
   * Navigate to login page
   */
  async goToLogin(): Promise<void> {
    await this.loginLink.click();
  }
}
