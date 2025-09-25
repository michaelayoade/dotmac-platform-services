import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should redirect to login when not authenticated', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/.*login/);
  });

  test('should show login form', async ({ page }) => {
    await page.goto('/login');

    // Check form elements exist
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should show error on invalid credentials', async ({ page }) => {
    await page.goto('/login');

    // Fill in invalid credentials
    await page.fill('input[name="username"]', 'invalid_user');
    await page.fill('input[name="password"]', 'wrong_password');
    await page.click('button[type="submit"]');

    // Check for error message
    await expect(page.locator('.error-message')).toBeVisible();
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.goto('/login');

    // Fill in valid test credentials
    await page.fill('input[name="username"]', 'john.doe');
    await page.fill('input[name="password"]', 'Test123!@#');
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await expect(page).toHaveURL(/.*dashboard/);

    // Should show user info
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('should logout successfully', async ({ page, context }) => {
    // Set auth cookies (simulate logged in state)
    await context.addCookies([
      {
        name: 'access_token',
        value: 'test_token',
        domain: 'localhost',
        path: '/',
      },
    ]);

    await page.goto('/dashboard');

    // Click logout button
    await page.click('[data-testid="logout-button"]');

    // Should redirect to login
    await expect(page).toHaveURL(/.*login/);

    // Cookies should be cleared
    const cookies = await context.cookies();
    const authCookie = cookies.find(c => c.name === 'access_token');
    expect(authCookie).toBeUndefined();
  });
});

test.describe('Registration Flow', () => {
  test('should navigate to registration page', async ({ page }) => {
    await page.goto('/login');
    await page.click('a[href="/register"]');
    await expect(page).toHaveURL(/.*register/);
  });

  test('should validate registration form', async ({ page }) => {
    await page.goto('/register');

    // Try to submit empty form
    await page.click('button[type="submit"]');

    // Should show validation errors
    await expect(page.locator('.field-error')).toHaveCount({ minimum: 3 });
  });

  test('should show password requirements', async ({ page }) => {
    await page.goto('/register');

    // Focus password field
    await page.focus('input[name="password"]');

    // Should show password requirements
    await expect(page.locator('.password-requirements')).toBeVisible();

    // Type weak password
    await page.fill('input[name="password"]', '123');

    // Should show password strength indicator
    await expect(page.locator('.password-strength-weak')).toBeVisible();

    // Type strong password
    await page.fill('input[name="password"]', 'Test123!@#');
    await expect(page.locator('.password-strength-strong')).toBeVisible();
  });

  test('should register new user', async ({ page }) => {
    await page.goto('/register');

    // Fill registration form
    const timestamp = Date.now();
    await page.fill('input[name="email"]', `test${timestamp}@example.com`);
    await page.fill('input[name="username"]', `testuser${timestamp}`);
    await page.fill('input[name="password"]', 'Test123!@#');
    await page.fill('input[name="confirmPassword"]', 'Test123!@#');
    await page.fill('input[name="firstName"]', 'Test');
    await page.fill('input[name="lastName"]', 'User');

    // Accept terms if present
    const termsCheckbox = page.locator('input[name="acceptTerms"]');
    if (await termsCheckbox.isVisible()) {
      await termsCheckbox.check();
    }

    // Submit form
    await page.click('button[type="submit"]');

    // Should redirect to login with success message
    await expect(page).toHaveURL(/.*login.*registered=true/);
    await expect(page.locator('.success-message')).toBeVisible();
  });
});

test.describe('Password Reset Flow', () => {
  test('should navigate to password reset', async ({ page }) => {
    await page.goto('/login');
    await page.click('a[href="/forgot-password"]');
    await expect(page).toHaveURL(/.*forgot-password/);
  });

  test('should request password reset', async ({ page }) => {
    await page.goto('/forgot-password');

    // Enter email
    await page.fill('input[name="email"]', 'john.doe@example.com');
    await page.click('button[type="submit"]');

    // Should show success message
    await expect(page.locator('.success-message')).toContainText('reset link has been sent');
  });

  test('should validate reset token', async ({ page }) => {
    // Navigate with invalid token
    await page.goto('/reset-password?token=invalid_token');

    // Should show error
    await expect(page.locator('.error-message')).toContainText('Invalid or expired token');
  });
});