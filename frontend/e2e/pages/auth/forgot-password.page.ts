import { Page, Locator } from "@playwright/test";
import { BasePage } from "../base.page";

/**
 * Forgot Password Page Object
 */
export class ForgotPasswordPage extends BasePage {
  readonly path = "/forgot-password";

  // Form elements
  readonly emailInput: Locator;
  readonly submitButton: Locator;
  readonly backToLoginLink: Locator;

  // Messages
  readonly successMessage: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    super(page);

    this.emailInput = page.locator('input[type="email"], input#email, input[name="email"]');
    this.submitButton = page.locator('button[type="submit"]');
    this.backToLoginLink = page.getByRole("link", { name: /back to login|sign in/i });

    this.successMessage = page.locator(".status-success, .bg-status-success, [data-testid='success']");
    this.errorMessage = page.locator(".status-error, .bg-status-error, [role='alert']");
  }

  /**
   * Request password reset
   */
  async requestReset(email: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.submitButton.click();
  }

  /**
   * Check if success message is shown
   */
  async isSuccessMessageVisible(): Promise<boolean> {
    return await this.successMessage.isVisible();
  }

  /**
   * Go back to login
   */
  async goBackToLogin(): Promise<void> {
    await this.backToLoginLink.click();
  }
}

/**
 * Reset Password Page Object
 */
export class ResetPasswordPage extends BasePage {
  readonly path = "/reset-password";

  // Form elements
  readonly newPasswordInput: Locator;
  readonly confirmPasswordInput: Locator;
  readonly submitButton: Locator;

  // Messages
  readonly successMessage: Locator;
  readonly errorMessage: Locator;
  readonly tokenExpiredMessage: Locator;

  constructor(page: Page) {
    super(page);

    this.newPasswordInput = page.locator('input#password, input[name="password"]').first();
    this.confirmPasswordInput = page.locator('input#confirmPassword, input[name="confirmPassword"]');
    this.submitButton = page.locator('button[type="submit"]');

    this.successMessage = page.locator(".status-success, .bg-status-success");
    this.errorMessage = page.locator(".status-error, .bg-status-error, [role='alert']");
    this.tokenExpiredMessage = page.locator('[data-testid="token-expired"]');
  }

  /**
   * Reset password with new password
   */
  async resetPassword(newPassword: string): Promise<void> {
    await this.newPasswordInput.fill(newPassword);
    if (await this.confirmPasswordInput.isVisible()) {
      await this.confirmPasswordInput.fill(newPassword);
    }
    await this.submitButton.click();
  }

  /**
   * Check if token expired message is shown
   */
  async isTokenExpired(): Promise<boolean> {
    return await this.tokenExpiredMessage.isVisible();
  }
}

/**
 * Verify Email Page Object
 */
export class VerifyEmailPage extends BasePage {
  readonly path = "/verify-email";

  // Messages
  readonly verifyingMessage: Locator;
  readonly successMessage: Locator;
  readonly errorMessage: Locator;

  // Actions
  readonly resendButton: Locator;
  readonly continueButton: Locator;

  constructor(page: Page) {
    super(page);

    this.verifyingMessage = page.locator('[data-testid="verifying"]');
    this.successMessage = page.locator(".status-success, .bg-status-success");
    this.errorMessage = page.locator(".status-error, .bg-status-error, [role='alert']");

    this.resendButton = page.getByRole("button", { name: /resend/i });
    this.continueButton = page.getByRole("button", { name: /continue/i });
  }

  /**
   * Check if verification was successful
   */
  async isVerificationSuccessful(): Promise<boolean> {
    return await this.successMessage.isVisible();
  }

  /**
   * Resend verification email
   */
  async resendVerification(): Promise<void> {
    await this.resendButton.click();
  }

  /**
   * Continue to app after verification
   */
  async continueToApp(): Promise<void> {
    await this.continueButton.click();
  }
}
