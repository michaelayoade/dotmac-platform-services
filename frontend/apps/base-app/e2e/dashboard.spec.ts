import { test, expect, Page } from '@playwright/test';

// Helper to login before tests
async function loginAsUser(page: Page, username = 'john.doe', password = 'Test123!@#') {
  await page.goto('/login');
  await page.fill('input[name="username"]', username);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForURL(/.*dashboard/);
}

test.describe('Dashboard Critical Flows', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await loginAsUser(page);
  });

  test('should display dashboard overview', async ({ page }) => {
    // Check main dashboard elements
    await expect(page.locator('h1')).toContainText('Dashboard');
    await expect(page.locator('[data-testid="stats-grid"]')).toBeVisible();
    await expect(page.locator('[data-testid="recent-activity"]')).toBeVisible();
  });

  test('should navigate to different sections', async ({ page }) => {
    // Navigate to Settings
    await page.click('a[href="/dashboard/settings"]');
    await expect(page).toHaveURL(/.*dashboard\/settings/);
    await expect(page.locator('h1')).toContainText('Settings');

    // Navigate to Profile
    await page.click('a[href="/dashboard/profile"]');
    await expect(page).toHaveURL(/.*dashboard\/profile/);
    await expect(page.locator('h1')).toContainText('Profile');

    // Navigate back to Overview
    await page.click('a[href="/dashboard"]');
    await expect(page).toHaveURL(/.*dashboard$/);
  });

  test('should load and display user data', async ({ page }) => {
    // Wait for data to load
    await page.waitForSelector('[data-testid="user-info"]');

    // Check user info is displayed
    const userInfo = page.locator('[data-testid="user-info"]');
    await expect(userInfo).toContainText('John Doe');
    await expect(userInfo).toContainText('john.doe@example.com');
  });

  test('should handle data refresh', async ({ page }) => {
    // Click refresh button
    await page.click('[data-testid="refresh-button"]');

    // Check loading state
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeVisible();

    // Wait for data to reload
    await page.waitForSelector('[data-testid="stats-grid"]');

    // Check data is updated (timestamp should change)
    const timestamp = await page.locator('[data-testid="last-updated"]').textContent();
    expect(timestamp).toBeTruthy();
  });

  test('should open and close modals', async ({ page }) => {
    // Open create modal
    await page.click('[data-testid="create-button"]');
    await expect(page.locator('[role="dialog"]')).toBeVisible();

    // Close with ESC key
    await page.keyboard.press('Escape');
    await expect(page.locator('[role="dialog"]')).not.toBeVisible();

    // Open again
    await page.click('[data-testid="create-button"]');

    // Close with close button
    await page.click('[data-testid="modal-close"]');
    await expect(page.locator('[role="dialog"]')).not.toBeVisible();
  });

  test('should handle form submissions', async ({ page }) => {
    // Open settings
    await page.goto('/dashboard/settings');

    // Update display name
    await page.fill('input[name="displayName"]', 'Updated Name');

    // Save changes
    await page.click('[data-testid="save-settings"]');

    // Check for success message
    await expect(page.locator('.success-toast')).toContainText('Settings saved');

    // Verify the change persisted
    await page.reload();
    await expect(page.locator('input[name="displayName"]')).toHaveValue('Updated Name');
  });

  test('should handle API errors gracefully', async ({ page, route }) => {
    // Mock API error
    await route('**/api/v1/dashboard/stats', route => {
      route.fulfill({
        status: 500,
        json: { error: 'Internal server error' },
      });
    });

    await page.goto('/dashboard');

    // Should show error message
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Failed to load data');

    // Should show retry button
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
  });

  test('should handle pagination', async ({ page }) => {
    await page.goto('/dashboard/items');

    // Check pagination controls exist
    await expect(page.locator('[data-testid="pagination"]')).toBeVisible();

    // Go to next page
    await page.click('[data-testid="next-page"]');
    await expect(page).toHaveURL(/.*page=2/);

    // Go to previous page
    await page.click('[data-testid="prev-page"]');
    await expect(page).toHaveURL(/.*page=1/);

    // Jump to specific page
    await page.click('[data-testid="page-3"]');
    await expect(page).toHaveURL(/.*page=3/);
  });

  test('should handle search and filtering', async ({ page }) => {
    await page.goto('/dashboard/items');

    // Search for items
    await page.fill('[data-testid="search-input"]', 'test query');
    await page.keyboard.press('Enter');

    // URL should update with search params
    await expect(page).toHaveURL(/.*search=test\+query/);

    // Apply filter
    await page.selectOption('[data-testid="status-filter"]', 'active');
    await expect(page).toHaveURL(/.*status=active/);

    // Clear filters
    await page.click('[data-testid="clear-filters"]');
    await expect(page).toHaveURL(/\/dashboard\/items$/);
  });

  test('should export data', async ({ page, download }) => {
    await page.goto('/dashboard/reports');

    // Trigger export
    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid="export-csv"]');
    const downloadedFile = await downloadPromise;

    // Verify download
    expect(downloadedFile.suggestedFilename()).toContain('.csv');
  });
});

test.describe('User Profile Management', () => {
  test.beforeEach(async ({ page }) => {
    await loginAsUser(page);
    await page.goto('/dashboard/profile');
  });

  test('should update profile information', async ({ page }) => {
    // Update fields
    await page.fill('input[name="firstName"]', 'Updated');
    await page.fill('input[name="lastName"]', 'User');
    await page.fill('textarea[name="bio"]', 'This is my updated bio');

    // Save
    await page.click('[data-testid="save-profile"]');

    // Check success
    await expect(page.locator('.success-toast')).toContainText('Profile updated');

    // Verify changes persisted
    await page.reload();
    await expect(page.locator('input[name="firstName"]')).toHaveValue('Updated');
  });

  test('should upload avatar', async ({ page }) => {
    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('./test-assets/avatar.jpg');

    // Check preview
    await expect(page.locator('[data-testid="avatar-preview"]')).toBeVisible();

    // Save
    await page.click('[data-testid="save-avatar"]');
    await expect(page.locator('.success-toast')).toContainText('Avatar updated');
  });

  test('should change password', async ({ page }) => {
    // Open password change form
    await page.click('[data-testid="change-password-btn"]');

    // Fill form
    await page.fill('input[name="currentPassword"]', 'Test123!@#');
    await page.fill('input[name="newPassword"]', 'NewTest123!@#');
    await page.fill('input[name="confirmPassword"]', 'NewTest123!@#');

    // Submit
    await page.click('[data-testid="update-password"]');

    // Check success
    await expect(page.locator('.success-toast')).toContainText('Password updated');
  });

  test('should enable two-factor authentication', async ({ page }) => {
    // Open 2FA settings
    await page.click('[data-testid="security-tab"]');
    await page.click('[data-testid="enable-2fa"]');

    // Should show QR code
    await expect(page.locator('[data-testid="2fa-qr-code"]')).toBeVisible();

    // Enter verification code (mock)
    await page.fill('input[name="verificationCode"]', '123456');
    await page.click('[data-testid="verify-2fa"]');

    // Check success
    await expect(page.locator('.success-toast')).toContainText('Two-factor authentication enabled');
    await expect(page.locator('[data-testid="2fa-status"]')).toContainText('Enabled');
  });
});