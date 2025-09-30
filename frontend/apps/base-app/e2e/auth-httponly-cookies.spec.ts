/**
 * End-to-end tests for HttpOnly cookie authentication flow
 */

import { test, expect } from '@playwright/test';

test.describe('HttpOnly Cookie Authentication', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
  });

  test('login flow sets HttpOnly cookies and redirects to dashboard', async ({ page, context }) => {
    // Fill in login form
    await page.fill('[data-testid="username-input"]', 'testuser');
    await page.fill('[data-testid="password-input"]', 'testpassword');

    // Intercept the login API call
    const loginPromise = page.waitForResponse('/api/v1/auth/login');

    // Submit login form
    await page.click('[data-testid="login-button"]');

    // Wait for login response
    const loginResponse = await loginPromise;
    expect(loginResponse.status()).toBe(200);

    // Check that cookies were set
    const cookies = await context.cookies();
    const accessCookie = cookies.find(cookie => cookie.name === 'access_token');
    const refreshCookie = cookies.find(cookie => cookie.name === 'refresh_token');

    expect(accessCookie).toBeDefined();
    expect(refreshCookie).toBeDefined();

    // Verify cookie security attributes
    expect(accessCookie!.httpOnly).toBe(true);
    expect(accessCookie!.sameSite).toBe('Strict');
    expect(refreshCookie!.httpOnly).toBe(true);
    expect(refreshCookie!.sameSite).toBe('Strict');

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');

    // Dashboard should be accessible without additional authentication
    await expect(page.locator('[data-testid="dashboard-content"]')).toBeVisible();
  });

  test('dashboard access without authentication redirects to login', async ({ page }) => {
    // Try to access dashboard directly without authentication
    await page.goto('/dashboard');

    // Should be redirected to login
    await expect(page).toHaveURL(/\/login/);
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
  });

  test('authenticated requests use HttpOnly cookies automatically', async ({ page, context }) => {
    // Login first
    await page.goto('/login');
    await page.fill('[data-testid="username-input"]', 'testuser');
    await page.fill('[data-testid="password-input"]', 'testpassword');
    await page.click('[data-testid="login-button"]');

    // Wait for redirect to dashboard
    await expect(page).toHaveURL('/dashboard');

    // Make API requests that require authentication
    const responsePromise = page.waitForResponse('/api/v1/auth/me');

    // Trigger an authenticated API call (e.g., loading user profile)
    await page.click('[data-testid="user-profile-button"]');

    const response = await responsePromise;
    expect(response.status()).toBe(200);

    // Verify the request was made with cookies, not Authorization header
    const request = response.request();
    const headers = await request.allHeaders();

    // Should NOT have Authorization header (using cookies instead)
    expect(headers.authorization).toBeUndefined();

    // Should have Cookie header with our tokens
    expect(headers.cookie).toContain('access_token=');
    expect(headers.cookie).toContain('refresh_token=');
  });

  test('token refresh happens automatically on 401', async ({ page, context }) => {
    // Login first
    await page.goto('/login');
    await page.fill('[data-testid="username-input"]', 'testuser');
    await page.fill('[data-testid="password-input"]', 'testpassword');
    await page.click('[data-testid="login-button"]');

    await expect(page).toHaveURL('/dashboard');

    // Manually expire the access token by clearing it (simulate expiry)
    await context.addCookies([{
      name: 'access_token',
      value: 'expired.token.value',
      domain: 'localhost',
      path: '/',
      httpOnly: true,
      sameSite: 'Strict'
    }]);

    // Set up request/response monitoring
    const refreshPromise = page.waitForResponse('/api/v1/auth/refresh');

    // Make a request that should trigger refresh
    await page.click('[data-testid="user-profile-button"]');

    // Should automatically attempt token refresh
    const refreshResponse = await refreshPromise;
    expect(refreshResponse.status()).toBe(200);

    // After refresh, the original request should succeed
    const profileResponse = await page.waitForResponse('/api/v1/auth/me');
    expect(profileResponse.status()).toBe(200);
  });

  test('logout clears HttpOnly cookies and redirects to login', async ({ page, context }) => {
    // Login first
    await page.goto('/login');
    await page.fill('[data-testid="username-input"]', 'testuser');
    await page.fill('[data-testid="password-input"]', 'testpassword');
    await page.click('[data-testid="login-button"]');

    await expect(page).toHaveURL('/dashboard');

    // Verify cookies are present
    let cookies = await context.cookies();
    expect(cookies.find(c => c.name === 'access_token')).toBeDefined();
    expect(cookies.find(c => c.name === 'refresh_token')).toBeDefined();

    // Intercept logout API call
    const logoutPromise = page.waitForResponse('/api/v1/auth/logout');

    // Logout
    await page.click('[data-testid="logout-button"]');

    // Wait for logout response
    const logoutResponse = await logoutPromise;
    expect(logoutResponse.status()).toBe(200);

    // Should redirect to login
    await expect(page).toHaveURL('/login');

    // Cookies should be cleared
    cookies = await context.cookies();
    const accessCookie = cookies.find(c => c.name === 'access_token');
    const refreshCookie = cookies.find(c => c.name === 'refresh_token');

    // Cookies should either be absent or have empty/expired values
    if (accessCookie) {
      expect(accessCookie.value).toBe('');
    }
    if (refreshCookie) {
      expect(refreshCookie.value).toBe('');
    }
  });

  test('multiple tabs share authentication state', async ({ browser }) => {
    // Create two browser contexts (tabs)
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();

    const page1 = await context1.newPage();
    const page2 = await context2.newPage();

    // Login in first tab
    await page1.goto('/login');
    await page1.fill('[data-testid="username-input"]', 'testuser');
    await page1.fill('[data-testid="password-input"]', 'testpassword');
    await page1.click('[data-testid="login-button"]');

    await expect(page1).toHaveURL('/dashboard');

    // Copy cookies from first context to second context
    const cookies = await context1.cookies();
    await context2.addCookies(cookies);

    // Second tab should be authenticated
    await page2.goto('/dashboard');
    await expect(page2).toHaveURL('/dashboard');
    await expect(page2.locator('[data-testid="dashboard-content"]')).toBeVisible();

    // Logout from first tab
    await page1.click('[data-testid="logout-button"]');

    // Second tab should become unauthenticated after next request
    await page2.reload();
    await expect(page2).toHaveURL(/\/login/);

    await context1.close();
    await context2.close();
  });

  test('registration flow sets HttpOnly cookies', async ({ page, context }) => {
    // Navigate to registration page
    await page.goto('/register');

    // Fill registration form
    await page.fill('[data-testid="username-input"]', 'newuser');
    await page.fill('[data-testid="email-input"]', 'newuser@example.com');
    await page.fill('[data-testid="password-input"]', 'strongpassword123');
    await page.fill('[data-testid="confirm-password-input"]', 'strongpassword123');

    // Submit registration
    const registerPromise = page.waitForResponse('/api/v1/auth/register');
    await page.click('[data-testid="register-button"]');

    const registerResponse = await registerPromise;
    expect(registerResponse.status()).toBe(200);

    // Should set HttpOnly cookies
    const cookies = await context.cookies();
    const accessCookie = cookies.find(cookie => cookie.name === 'access_token');
    const refreshCookie = cookies.find(cookie => cookie.name === 'refresh_token');

    expect(accessCookie).toBeDefined();
    expect(refreshCookie).toBeDefined();
    expect(accessCookie!.httpOnly).toBe(true);
    expect(refreshCookie!.httpOnly).toBe(true);

    // Should redirect to dashboard (automatic login after registration)
    await expect(page).toHaveURL('/dashboard');
  });

  test('password reset flow does not auto-login', async ({ page, context }) => {
    // Go to password reset page
    await page.goto('/forgot-password');

    // Submit password reset request
    await page.fill('[data-testid="email-input"]', 'testuser@example.com');
    await page.click('[data-testid="reset-password-button"]');

    // Should show success message but not set cookies
    await expect(page.locator('[data-testid="reset-success-message"]')).toBeVisible();

    const cookies = await context.cookies();
    expect(cookies.find(c => c.name === 'access_token')).toBeUndefined();
    expect(cookies.find(c => c.name === 'refresh_token')).toBeUndefined();

    // Should still be on reset page or redirect to login
    expect(page.url()).toMatch(/\/(forgot-password|login)/);
  });

  test('XSS protection - cookies not accessible via JavaScript', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('[data-testid="username-input"]', 'testuser');
    await page.fill('[data-testid="password-input"]', 'testpassword');
    await page.click('[data-testid="login-button"]');

    await expect(page).toHaveURL('/dashboard');

    // Try to access cookies via JavaScript (should fail due to HttpOnly)
    const cookieValue = await page.evaluate(() => {
      // Try to read HttpOnly cookies - should not be accessible
      return document.cookie;
    });

    // HttpOnly cookies should not be accessible via document.cookie
    expect(cookieValue).not.toContain('access_token=');
    expect(cookieValue).not.toContain('refresh_token=');
  });
});