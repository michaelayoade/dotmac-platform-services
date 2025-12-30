import { Page, Locator } from "@playwright/test";
import { BasePage } from "../base.page";

/**
 * Login Page Object
 */
export class LoginPage extends BasePage {
  readonly path = "/login";

  // Form elements
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly rememberMeCheckbox: Locator;
  readonly forgotPasswordLink: Locator;
  readonly showPasswordButton: Locator;

  // 2FA elements
  readonly twoFactorCodeInput: Locator;
  readonly verifyButton: Locator;
  readonly useBackupCodeCheckbox: Locator;

  // Error display
  readonly errorMessage: Locator;

  // Branding
  readonly brandingLabel: Locator;
  readonly heading: Locator;
  readonly subheading: Locator;

  constructor(page: Page) {
    super(page);

    // Form elements
    this.emailInput = page.locator('input[type="email"], input#email, input[name="email"]');
    this.passwordInput = page.locator('input[type="password"], input#password, input[name="password"]');
    this.submitButton = page.locator('button[type="submit"]');
    this.rememberMeCheckbox = page.locator('input#remember-me, input[name="rememberMe"]');
    this.forgotPasswordLink = page.getByRole("link", { name: /forgot password/i });
    this.showPasswordButton = page.locator('button[aria-label*="password"]');

    // 2FA elements
    this.twoFactorCodeInput = page.locator('input#two-factor-code, input[name="twoFactorCode"]');
    this.verifyButton = page.getByRole("button", { name: /verify/i });
    this.useBackupCodeCheckbox = page.locator('input#use-backup-code, input[name="useBackupCode"]');

    // Error display
    this.errorMessage = page.locator(".status-error, .bg-status-error, [role='alert']");

    // Branding
    this.brandingLabel = page.locator(".font-semibold.text-xl");
    this.heading = page.locator("h1");
    this.subheading = page.locator("h1 + p");
  }

  /**
   * Login with email and password
   */
  async login(email: string, password: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  /**
   * Login with remember me option
   */
  async loginWithRemember(email: string, password: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.rememberMeCheckbox.check();
    await this.submitButton.click();
  }

  /**
   * Enter 2FA verification code
   */
  async enterTwoFactorCode(code: string, isBackupCode: boolean = false): Promise<void> {
    if (isBackupCode) {
      await this.useBackupCodeCheckbox.check();
    }
    await this.twoFactorCodeInput.fill(code);
    await this.verifyButton.click();
  }

  /**
   * Get error message text
   */
  async getErrorMessageText(): Promise<string | null> {
    if (await this.errorMessage.isVisible()) {
      return await this.errorMessage.textContent();
    }
    return null;
  }

  /**
   * Check if login form is visible
   */
  async isLoginFormVisible(): Promise<boolean> {
    return (
      (await this.emailInput.isVisible()) && (await this.passwordInput.isVisible())
    );
  }

  /**
   * Check if 2FA form is visible
   */
  async isTwoFactorFormVisible(): Promise<boolean> {
    return await this.twoFactorCodeInput.isVisible();
  }

  /**
   * Toggle password visibility
   */
  async togglePasswordVisibility(): Promise<void> {
    await this.showPasswordButton.click();
  }

  /**
   * Navigate to forgot password page
   */
  async goToForgotPassword(): Promise<void> {
    await this.forgotPasswordLink.click();
  }
}
