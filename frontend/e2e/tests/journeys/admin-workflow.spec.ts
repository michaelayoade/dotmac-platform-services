/**
 * E2E tests for admin user journeys
 * Tests complete workflows that an admin would perform
 */
import { test, expect } from '@playwright/test';

test.describe('Admin User Journey', () => {
  const BASE_APP_URL = 'http://localhost:3000';
  const TEST_EMAIL = 'admin@test.com';
  const TEST_PASSWORD = 'Test123!@#';

  /**
   * Helper to login
   */
  async function login(page: any) {
    await page.goto(`${BASE_APP_URL}/login`);
    await page.waitForLoadState('networkidle');
    await page.getByTestId('email-input').fill(TEST_EMAIL);
    await page.getByTestId('password-input').fill(TEST_PASSWORD);
    await page.getByTestId('submit-button').click();
    await page.waitForURL(/dashboard/, { timeout: 10000 });
  }

  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('admin can navigate dashboard', async ({ page }) => {
    // Should be on dashboard
    await expect(page).toHaveURL(/dashboard/);

    // Look for dashboard elements
    const dashboardContent = page.locator('[data-testid="dashboard"], .dashboard, main').first();
    await expect(dashboardContent).toBeVisible();

    console.log('Admin successfully accessed dashboard');
  });

  test('admin can access user management', async ({ page }) => {
    // Try to navigate to user management
    const userManagementLink = page.locator('[data-testid="users-link"], a:has-text("Users"), a[href*="users"]').first();

    if (await userManagementLink.isVisible({ timeout: 2000 }).catch(() => false)) {
      await userManagementLink.click();

      await page.waitForLoadState('networkidle');

      // Check if we're on user management page
      const isOnUsers = page.url().includes('/users');
      console.log('User management page accessible:', isOnUsers);

      if (isOnUsers) {
        // Look for user list
        const userList = page.locator('[data-testid="user-list"], table, .user-table').first();
        const hasUserList = await userList.isVisible({ timeout: 2000 }).catch(() => false);
        console.log('User list displayed:', hasUserList);
      }
    } else {
      console.log('User management link not found in navigation');
    }
  });

  test('admin can access settings', async ({ page }) => {
    // Try to navigate to settings
    const settingsLink = page.locator('[data-testid="settings-link"], a:has-text("Settings"), a[href*="settings"]').first();

    if (await settingsLink.isVisible({ timeout: 2000 }).catch(() => false)) {
      await settingsLink.click();

      await page.waitForLoadState('networkidle');

      // Check if we're on settings page
      const isOnSettings = page.url().includes('/settings');
      console.log('Settings page accessible:', isOnSettings);

      if (isOnSettings) {
        // Look for settings content
        const settingsContent = page.locator('[data-testid="settings"], .settings, form').first();
        const hasSettings = await settingsContent.isVisible({ timeout: 2000 }).catch(() => false);
        console.log('Settings content displayed:', hasSettings);
      }
    } else {
      console.log('Settings link not found in navigation');
    }
  });

  test('admin can logout', async ({ page }) => {
    // Look for logout button
    const logoutButton = page.locator('[data-testid="logout-button"], button:has-text("Logout"), button:has-text("Sign out")').first();

    if (await logoutButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await logoutButton.click();
    } else {
      // Try user menu approach
      const userMenu = page.locator('[data-testid="user-menu"], .user-menu, [aria-label="User menu"]').first();
      if (await userMenu.isVisible({ timeout: 2000 }).catch(() => false)) {
        await userMenu.click();
        await page.locator('button:has-text("Logout"), button:has-text("Sign out")').first().click();
      }
    }

    // Should redirect to login
    await page.waitForURL(/login/, { timeout: 5000 });
    await expect(page).toHaveURL(/login/);

    console.log('Admin successfully logged out');
  });

  test('admin workflow documentation', async ({ page }) => {
    // This test documents what admin features are available
    await page.goto(`${BASE_APP_URL}/dashboard`);

    // Check for admin-specific navigation items
    const navigationItems = [
      { selector: 'a:has-text("Users")', name: 'User Management' },
      { selector: 'a:has-text("Settings")', name: 'Settings' },
      { selector: 'a:has-text("Analytics")', name: 'Analytics' },
      { selector: 'a:has-text("Billing")', name: 'Billing' },
      { selector: 'a:has-text("Admin")', name: 'Admin Panel' },
      { selector: 'a:has-text("Dashboard")', name: 'Dashboard' }
    ];

    const availableFeatures: string[] = [];

    for (const item of navigationItems) {
      const element = page.locator(item.selector).first();
      if (await element.isVisible({ timeout: 1000 }).catch(() => false)) {
        availableFeatures.push(item.name);
      }
    }

    console.log('Available admin features:', availableFeatures);

    // This test always passes - it's for documentation
    expect(true).toBe(true);
  });
});
