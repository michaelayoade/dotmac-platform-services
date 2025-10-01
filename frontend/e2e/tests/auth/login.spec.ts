import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';

test.describe('Authentication Flow', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    await loginPage.goto();
  });

  test('should display login form', async ({ page }) => {
    await expect(page).toHaveTitle(/Login/);
    await expect(loginPage.emailInput).toBeVisible();
    await expect(loginPage.passwordInput).toBeVisible();
    await expect(loginPage.loginButton).toBeVisible();
  });

  test('should login with valid credentials', async ({ page }) => {
    await loginPage.login('admin@test.com', 'Test123!@#');

    // Should redirect to dashboard
    await expect(page).toHaveURL(/dashboard/);
    await expect(dashboardPage.welcomeMessage).toBeVisible();

    // Should display user info
    await expect(dashboardPage.userMenu).toContainText('Test Admin');
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await loginPage.login('admin@test.com', 'wrongpassword');

    // Should stay on login page
    await expect(page).toHaveURL(/login/);
    await expect(loginPage.errorMessage).toBeVisible();
    await expect(loginPage.errorMessage).toContainText('Invalid credentials');
  });

  test('should show validation errors for empty fields', async ({ page }) => {
    await loginPage.loginButton.click();

    await expect(loginPage.emailError).toBeVisible();
    await expect(loginPage.passwordError).toBeVisible();
    await expect(loginPage.emailError).toContainText('Email is required');
    await expect(loginPage.passwordError).toContainText('Password is required');
  });

  test('should show validation error for invalid email format', async ({ page }) => {
    await loginPage.fillEmail('invalid-email');
    await loginPage.fillPassword('Test123!@#');
    await loginPage.loginButton.click();

    await expect(loginPage.emailError).toBeVisible();
    await expect(loginPage.emailError).toContainText('Invalid email format');
  });

  test('should handle "Remember Me" functionality', async ({ page, context }) => {
    await loginPage.toggleRememberMe();
    await loginPage.login('admin@test.com', 'Test123!@#');

    // Check that remember me cookie is set
    const cookies = await context.cookies();
    const rememberMeCookie = cookies.find(cookie => cookie.name === 'remember_me');
    expect(rememberMeCookie).toBeDefined();
    expect(rememberMeCookie?.value).toBe('true');
  });

  test('should redirect to intended page after login', async ({ page }) => {
    // Try to access protected page
    await page.goto('/admin/users');

    // Should redirect to login
    await expect(page).toHaveURL(/login/);

    // Login
    await loginPage.login('admin@test.com', 'Test123!@#');

    // Should redirect back to intended page
    await expect(page).toHaveURL(/admin\/users/);
  });

  test('should handle forgot password link', async ({ page }) => {
    await loginPage.forgotPasswordLink.click();

    await expect(page).toHaveURL(/forgot-password/);
    await expect(page.locator('h1')).toContainText('Reset Password');
  });

  test('should handle sign up link', async ({ page }) => {
    await loginPage.signUpLink.click();

    await expect(page).toHaveURL(/register/);
    await expect(page.locator('h1')).toContainText('Create Account');
  });

  test('should handle network errors gracefully', async ({ page }) => {
    // Intercept login request and simulate network error
    await page.route('**/auth/login', route => {
      route.abort('failed');
    });

    await loginPage.login('admin@test.com', 'Test123!@#');

    await expect(loginPage.errorMessage).toBeVisible();
    await expect(loginPage.errorMessage).toContainText('Network error');
  });

  test('should show loading state during login', async ({ page }) => {
    // Intercept login request and delay response
    await page.route('**/auth/login', async route => {
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.continue();
    });

    await loginPage.fillEmail('admin@test.com');
    await loginPage.fillPassword('Test123!@#');
    await loginPage.loginButton.click();

    // Check loading state
    await expect(loginPage.loginButton).toBeDisabled();
    await expect(loginPage.loadingSpinner).toBeVisible();
    await expect(loginPage.loginButton).toContainText('Signing in...');
  });

  test('should handle rate limiting', async ({ page }) => {
    // Make multiple failed login attempts
    for (let i = 0; i < 5; i++) {
      await loginPage.login('admin@test.com', 'wrongpassword');
      await expect(loginPage.errorMessage).toBeVisible();
    }

    // Next attempt should be rate limited
    await loginPage.login('admin@test.com', 'wrongpassword');
    await expect(loginPage.errorMessage).toContainText('Too many login attempts');
  });

  test('should maintain CSRF protection', async ({ page }) => {
    // Check that CSRF token is present
    const csrfToken = await page.locator('input[name="csrf_token"]');
    await expect(csrfToken).toBeHidden(); // Hidden input

    const tokenValue = await csrfToken.getAttribute('value');
    expect(tokenValue).toBeTruthy();
    expect(tokenValue.length).toBeGreaterThan(10);
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await loginPage.login('admin@test.com', 'Test123!@#');
    await expect(page).toHaveURL(/dashboard/);

    // Logout
    await dashboardPage.logout();

    // Should redirect to login
    await expect(page).toHaveURL(/login/);
    await expect(loginPage.emailInput).toBeVisible();

    // Should clear session
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/login/); // Should redirect back to login
  });

  test('should handle session expiration', async ({ page }) => {
    // Login
    await loginPage.login('admin@test.com', 'Test123!@#');
    await expect(page).toHaveURL(/dashboard/);

    // Simulate token expiration
    await page.evaluate(() => {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    });

    // Try to access protected resource
    await page.goto('/admin/users');

    // Should redirect to login
    await expect(page).toHaveURL(/login/);
    await expect(loginPage.sessionExpiredMessage).toBeVisible();
  });
});