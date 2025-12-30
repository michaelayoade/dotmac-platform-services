import { test, expect, Page } from "@playwright/test";
import { LoginPage, SignupPage, ForgotPasswordPage } from "../../pages/auth";
import { expectLoadingComplete, expectNoErrors } from "../../utils/assertions";
import { PORTAL_URLS, STATIC_AUTH_ROUTES } from "../../utils/test-data";
import { mockAuthSuccess, mockAuthFailure, mock2FARequired } from "../../utils/api-mocks";

async function submitForm(page: Page): Promise<void> {
  await page.locator("form").first().evaluate((form) => {
    if (form instanceof HTMLFormElement) {
      form.requestSubmit();
    }
  });
}

test.describe("Authentication Smoke Tests", () => {
  test.describe("Login Page", () => {
    test("should display login page correctly", async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.navigate();

      await expect(loginPage.emailInput).toBeVisible();
      await expect(loginPage.passwordInput).toBeVisible();
      await expect(loginPage.submitButton).toBeVisible();
      await expect(loginPage.forgotPasswordLink).toBeVisible();
    });

    test("should show validation errors for empty form", async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.navigate();

      await submitForm(page);

      // Should show validation errors
      const errors = page.locator('[role="alert"]');
      await expect(errors.first()).toBeVisible();
      await expect(errors.filter({ hasText: /email|password/i }).first()).toBeVisible();
    });

    test("should show error for invalid credentials", async ({ page }) => {
      await mockAuthFailure(page, "Invalid email or password");

      const loginPage = new LoginPage(page);
      await loginPage.navigate();

      await loginPage.login("invalid@email.com", "wrongpassword");

      await expect(loginPage.errorMessage).toBeVisible();
    });

    test("should redirect to dashboard after successful login", async ({ page }) => {
      await mockAuthSuccess(page);

      const loginPage = new LoginPage(page);
      await loginPage.navigate();

      await loginPage.login("admin@test.local", "TestPassword123!");

      // Should redirect to dashboard
      await page.waitForURL("/");
    });

    test("should show 2FA form when required", async ({ page }) => {
      await mock2FARequired(page, "test-user-id");

      const loginPage = new LoginPage(page);
      await loginPage.navigate();

      await Promise.all([
        page.waitForResponse("**/api/v1/auth/login/cookie"),
        loginPage.login("admin@test.local", "TestPassword123!"),
      ]);

      await expect(loginPage.twoFactorCodeInput).toBeVisible();
      await expect(loginPage.verifyButton).toBeVisible();
    });

    test("should toggle password visibility", async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.navigate();

      await loginPage.passwordInput.fill("mypassword");

      // Initially password type
      await expect(loginPage.passwordInput).toHaveAttribute("type", "password");

      // Toggle visibility
      await loginPage.togglePasswordVisibility();

      // Should be text type now
      await expect(loginPage.passwordInput).toHaveAttribute("type", "text");
    });

    test("should navigate to forgot password", async ({ page }) => {
      const loginPage = new LoginPage(page);
      await loginPage.navigate();

      await loginPage.goToForgotPassword();

      await expect(page).toHaveURL(/forgot-password/);
    });
  });

  test.describe("Signup Page", () => {
    test("should display signup page correctly", async ({ page }) => {
      const signupPage = new SignupPage(page);
      await signupPage.navigate();

      await expect(signupPage.emailInput).toBeVisible();
      await expect(signupPage.passwordInput).toBeVisible();
      await expect(signupPage.submitButton).toBeVisible();
    });

    test("should show validation for weak password", async ({ page }) => {
      const signupPage = new SignupPage(page);
      await signupPage.navigate();

      await signupPage.passwordInput.fill("123");
      await submitForm(page);

      // Should show password validation error
      await expect(
        page.locator('[role="alert"]').filter({ hasText: /password/i }).first()
      ).toBeVisible();
    });

    test("should have link to login", async ({ page }) => {
      const signupPage = new SignupPage(page);
      await signupPage.navigate();

      await signupPage.goToLogin();

      await expect(page).toHaveURL(/login/);
    });
  });

  test.describe("Forgot Password Page", () => {
    test("should display forgot password page correctly", async ({ page }) => {
      const forgotPage = new ForgotPasswordPage(page);
      await forgotPage.navigate();

      await expect(forgotPage.emailInput).toBeVisible();
      await expect(forgotPage.submitButton).toBeVisible();
      await expect(forgotPage.backToLoginLink).toBeVisible();
    });

    test("should show validation for invalid email", async ({ page }) => {
      const forgotPage = new ForgotPasswordPage(page);
      await forgotPage.navigate();

      await forgotPage.emailInput.fill("invalid-email");
      await submitForm(page);

      // Should show email validation error
      await expect(
        page.locator('[role="alert"]').filter({ hasText: /email/i }).first()
      ).toBeVisible();
    });

    test("should navigate back to login", async ({ page }) => {
      const forgotPage = new ForgotPasswordPage(page);
      await forgotPage.navigate();

      await forgotPage.goBackToLogin();

      await expect(page).toHaveURL(/login/);
    });
  });

  test.describe("All Auth Pages Load", () => {
    for (const route of STATIC_AUTH_ROUTES) {
      test(`should load ${route.name} page`, async ({ page }) => {
        await page.goto(route.path);
        await expectLoadingComplete(page);

        // Page should render a heading for the auth surface
        await expect(page.locator("h1, h2").first()).toBeVisible();
      });
    }
  });
});

test.describe("Partner Login", () => {
  test("should display partner login page", async ({ page }) => {
    await page.goto(PORTAL_URLS.partner.login);

    await expect(page.locator('input[type="email"], input#email')).toBeVisible();
    await expect(page.locator('input[type="password"], input#password')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test("should show partner branding", async ({ page }) => {
    await page.goto(PORTAL_URLS.partner.login);

    // Should have partner-specific branding or text
    await expect(page.getByText("Partner Portal", { exact: true })).toBeVisible();
  });
});

test.describe("Portal Login", () => {
  test("should display portal login page", async ({ page }) => {
    await page.goto(PORTAL_URLS.portal.login);

    await expect(page.locator('input[type="email"], input#email')).toBeVisible();
    await expect(page.locator('input[type="password"], input#password')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });
});
