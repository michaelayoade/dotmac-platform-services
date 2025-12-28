import { test, expect } from "@playwright/test";
import { LoginPage } from "../../pages/auth";
import { expectLoadingComplete } from "../../utils/assertions";
import {
  mockAuthSuccess,
  mockAuthFailure,
  mock2FARequired,
  mock2FAVerifySuccess,
} from "../../utils/api-mocks";
import { TEST_USERS } from "../../utils/test-data";

test.describe("Login Flow Tests", () => {
  test.describe("Successful Login", () => {
    test("should login with valid credentials and redirect to dashboard", async ({ page }) => {
      await mockAuthSuccess(page);

      const loginPage = new LoginPage(page);
      await loginPage.navigate();

      await loginPage.login(TEST_USERS.admin.email, TEST_USERS.admin.password);

      await page.waitForURL("/");
      await expectLoadingComplete(page);

      // Should be on dashboard
      await expect(page).toHaveURL("/");
    });

    test("should persist session with remember me", async ({ page }) => {
      await mockAuthSuccess(page);

      const loginPage = new LoginPage(page);
      await loginPage.navigate();

      await loginPage.loginWithRemember(TEST_USERS.admin.email, TEST_USERS.admin.password);

      await page.waitForURL("/");

      // Check for persistent cookie
      const cookies = await page.context().cookies();
      const sessionCookie = cookies.find((c) => c.name === "access_token" || c.name === "session");
      expect(sessionCookie).toBeDefined();
    });
  });

  test.describe("Failed Login", () => {
    test("should show error for invalid credentials", async ({ page }) => {
      await mockAuthFailure(page, "Invalid email or password");

      const loginPage = new LoginPage(page);
      await loginPage.navigate();

      await loginPage.login("wrong@email.com", "wrongpassword");

      await expect(loginPage.errorMessage).toBeVisible();
      const errorText = await loginPage.getErrorMessageText();
      expect(errorText).toContain("Invalid");
    });

    test("should show error for empty email", async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.navigate();

      await loginPage.passwordInput.fill("somepassword");
      await loginPage.submitButton.click();

      // Should show validation error
      await expect(page.locator("text=/email|required/i")).toBeVisible();
    });

    test("should show error for empty password", async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.navigate();

      await loginPage.emailInput.fill("user@example.com");
      await loginPage.submitButton.click();

      // Should show validation error
      await expect(page.locator("text=/password|required/i")).toBeVisible();
    });

    test("should show error for invalid email format", async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.navigate();

      await loginPage.emailInput.fill("invalid-email");
      await loginPage.passwordInput.fill("password123");
      await loginPage.submitButton.click();

      // Should show validation error for email format
      await expect(page.locator("text=/valid email/i")).toBeVisible();
    });
  });

  test.describe("Two-Factor Authentication", () => {
    test("should show 2FA form when required", async ({ page }) => {
      await mock2FARequired(page, "test-user-id");

      const loginPage = new LoginPage(page);
      await loginPage.navigate();

      await loginPage.login(TEST_USERS.admin.email, TEST_USERS.admin.password);

      // Should show 2FA form
      await expect(loginPage.twoFactorCodeInput).toBeVisible();
      await expect(loginPage.verifyButton).toBeVisible();
    });

    test("should complete login with valid 2FA code", async ({ page }) => {
      // First mock 2FA required
      await mock2FARequired(page, "test-user-id");

      const loginPage = new LoginPage(page);
      await loginPage.navigate();

      await loginPage.login(TEST_USERS.admin.email, TEST_USERS.admin.password);

      // Wait for 2FA form
      await expect(loginPage.twoFactorCodeInput).toBeVisible();

      // Now mock successful 2FA verification
      await mock2FAVerifySuccess(page);

      await loginPage.enterTwoFactorCode("123456");

      await page.waitForURL("/");
    });

    test("should allow using backup code", async ({ page }) => {
      await mock2FARequired(page, "test-user-id");

      const loginPage = new LoginPage(page);
      await loginPage.navigate();

      await loginPage.login(TEST_USERS.admin.email, TEST_USERS.admin.password);

      await expect(loginPage.twoFactorCodeInput).toBeVisible();
      await expect(loginPage.useBackupCodeCheckbox).toBeVisible();

      // Toggle backup code mode
      await loginPage.useBackupCodeCheckbox.check();
      await expect(loginPage.useBackupCodeCheckbox).toBeChecked();
    });
  });

  test.describe("Password Visibility", () => {
    test("should toggle password visibility", async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.navigate();

      await loginPage.passwordInput.fill("mypassword");

      // Initially hidden
      await expect(loginPage.passwordInput).toHaveAttribute("type", "password");

      // Toggle to show
      await loginPage.togglePasswordVisibility();
      await expect(loginPage.passwordInput).toHaveAttribute("type", "text");

      // Toggle to hide
      await loginPage.togglePasswordVisibility();
      await expect(loginPage.passwordInput).toHaveAttribute("type", "password");
    });
  });

  test.describe("Navigation", () => {
    test("should navigate to forgot password", async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.navigate();

      await loginPage.goToForgotPassword();

      await expect(page).toHaveURL(/forgot-password/);
    });

    test("should handle callback URL after login", async ({ page }) => {
      await mockAuthSuccess(page);

      // Navigate to login with callback URL
      await page.goto("/login?callbackUrl=/billing");

      const loginPage = new LoginPage(page);
      await loginPage.login(TEST_USERS.admin.email, TEST_USERS.admin.password);

      // Should redirect to the callback URL
      await page.waitForURL(/billing/);
    });
  });
});
