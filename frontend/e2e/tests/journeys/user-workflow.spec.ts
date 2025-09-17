import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';
import { ProfilePage } from '../pages/ProfilePage';
import { FilesPage } from '../pages/FilesPage';

test.describe('Regular User Journey', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;
  let profilePage: ProfilePage;
  let filesPage: FilesPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    profilePage = new ProfilePage(page);
    filesPage = new FilesPage(page);

    // Login as regular user
    await loginPage.goto();
    await loginPage.login('user@test.com', 'Test123!@#');
    await expect(page).toHaveURL(/dashboard/);
  });

  test('complete profile management workflow', async ({ page }) => {
    // Navigate to profile
    await dashboardPage.navigateToProfile();
    await expect(page).toHaveURL(/profile/);

    // Verify current profile information
    await expect(profilePage.emailField).toHaveValue('user@test.com');
    await expect(profilePage.fullNameField).toHaveValue('Test User');

    // Update profile information
    await profilePage.updateProfile({
      fullName: 'Updated Test User',
      phone: '+1234567890',
      bio: 'This is my updated bio for E2E testing',
      timezone: 'America/New_York'
    });

    await profilePage.saveProfile();

    // Verify update success
    await expect(page.locator('.success-message')).toContainText('Profile updated successfully');

    // Verify changes are saved
    await page.reload();
    await expect(profilePage.fullNameField).toHaveValue('Updated Test User');
    await expect(profilePage.phoneField).toHaveValue('+1234567890');
    await expect(profilePage.bioField).toHaveValue('This is my updated bio for E2E testing');

    // Upload profile picture
    await profilePage.uploadProfilePicture('test-avatar.jpg');

    // Verify upload success
    await expect(page.locator('.success-message')).toContainText('Profile picture updated');
    await expect(profilePage.profileImage).toBeVisible();

    // Update password
    await profilePage.navigateToPasswordTab();
    await profilePage.changePassword({
      currentPassword: 'Test123!@#',
      newPassword: 'NewTest123!@#',
      confirmPassword: 'NewTest123!@#'
    });

    // Verify password change
    await expect(page.locator('.success-message')).toContainText('Password updated successfully');

    // Test new password by logging out and back in
    await dashboardPage.logout();
    await expect(page).toHaveURL(/login/);

    await loginPage.login('user@test.com', 'NewTest123!@#');
    await expect(page).toHaveURL(/dashboard/);

    // Set up MFA
    await dashboardPage.navigateToProfile();
    await profilePage.navigateToSecurityTab();

    await profilePage.enableMFA();
    await expect(page.locator('.mfa-setup-modal')).toBeVisible();

    // Save backup codes
    await expect(page.locator('[data-testid="backup-codes"]')).toBeVisible();
    await page.click('[data-testid="download-backup-codes"]');

    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid="save-backup-codes"]');

    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('backup-codes');

    // Verify MFA setup completion
    await expect(page.locator('.success-message')).toContainText('Two-factor authentication enabled');
    await expect(page.locator('[data-testid="mfa-status"]')).toContainText('Enabled');

    // Configure notification preferences
    await profilePage.navigateToNotificationsTab();

    await profilePage.updateNotificationSettings({
      emailDigest: true,
      pushNotifications: false,
      smsAlerts: true,
      marketingEmails: false
    });

    await profilePage.saveNotificationSettings();
    await expect(page.locator('.success-message')).toContainText('Notification preferences updated');

    // Set up API keys
    await profilePage.navigateToAPIKeysTab();

    await profilePage.createAPIKey({
      name: 'E2E Test Key',
      scopes: ['read:profile', 'write:files'],
      expiresIn: '90 days'
    });

    // Verify API key creation
    await expect(page.locator('.success-message')).toContainText('API key created');
    await expect(page.locator('[data-testid="api-key-list"]')).toContainText('E2E Test Key');

    // Copy API key
    await page.click('[data-testid="copy-api-key"]');
    await expect(page.locator('.info-message')).toContainText('API key copied to clipboard');
  });

  test('file management workflow', async ({ page }) => {
    // Navigate to files
    await dashboardPage.navigateToFiles();
    await expect(page).toHaveURL(/files/);

    // Verify files interface
    await expect(filesPage.uploadArea).toBeVisible();
    await expect(filesPage.fileList).toBeVisible();

    // Upload a single file
    await filesPage.uploadFile('test-document.pdf');

    // Verify upload progress
    await expect(page.locator('.upload-progress')).toBeVisible();
    await expect(page.locator('.upload-progress')).not.toBeVisible();

    // Verify file appears in list
    await expect(page.locator('[data-filename="test-document.pdf"]')).toBeVisible();
    await expect(page.locator('.success-message')).toContainText('File uploaded successfully');

    // Upload multiple files
    await filesPage.uploadMultipleFiles(['image1.jpg', 'image2.png', 'document.docx']);

    // Verify all files uploaded
    await expect(page.locator('[data-filename="image1.jpg"]')).toBeVisible();
    await expect(page.locator('[data-filename="image2.png"]')).toBeVisible();
    await expect(page.locator('[data-filename="document.docx"]')).toBeVisible();

    // Create folder
    await filesPage.createFolder('E2E Test Folder');
    await expect(page.locator('[data-folder-name="E2E Test Folder"]')).toBeVisible();

    // Move file to folder
    await filesPage.selectFile('test-document.pdf');
    await filesPage.moveToFolder('E2E Test Folder');

    // Verify file moved
    await filesPage.openFolder('E2E Test Folder');
    await expect(page.locator('[data-filename="test-document.pdf"]')).toBeVisible();

    // Navigate back to root
    await filesPage.navigateToRoot();

    // Search for files
    await filesPage.searchFiles('image');
    await expect(page.locator('[data-filename="image1.jpg"]')).toBeVisible();
    await expect(page.locator('[data-filename="image2.png"]')).toBeVisible();
    await expect(page.locator('[data-filename="document.docx"]')).not.toBeVisible();

    // Clear search
    await filesPage.clearSearch();
    await expect(page.locator('[data-filename="document.docx"]')).toBeVisible();

    // Sort files
    await filesPage.sortBy('name');
    // Verify sorting order (implementation depends on your UI)

    await filesPage.sortBy('date');
    // Verify sorting by date

    // Filter by file type
    await filesPage.filterByType('images');
    await expect(page.locator('[data-filename="image1.jpg"]')).toBeVisible();
    await expect(page.locator('[data-filename="image2.png"]')).toBeVisible();
    await expect(page.locator('[data-filename="document.docx"]')).not.toBeVisible();

    // Clear filter
    await filesPage.clearFilters();

    // Share file
    await filesPage.shareFile('image1.jpg');
    await expect(page.locator('.share-modal')).toBeVisible();

    await page.fill('[data-testid="share-email"]', 'colleague@test.com');
    await page.selectOption('[data-testid="permission-level"]', 'view');
    await page.click('[data-testid="send-share"]');

    await expect(page.locator('.success-message')).toContainText('File shared successfully');

    // Generate public link
    await filesPage.generatePublicLink('image2.png');
    await expect(page.locator('.public-link-modal')).toBeVisible();

    await page.click('[data-testid="copy-public-link"]');
    await expect(page.locator('.info-message')).toContainText('Link copied to clipboard');

    // Download file
    const downloadPromise = page.waitForEvent('download');
    await filesPage.downloadFile('document.docx');
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toBe('document.docx');

    // Delete file
    await filesPage.deleteFile('image1.jpg');
    await expect(page.locator('.confirmation-modal')).toBeVisible();
    await page.click('[data-testid="confirm-delete"]');

    await expect(page.locator('.success-message')).toContainText('File deleted successfully');
    await expect(page.locator('[data-filename="image1.jpg"]')).not.toBeVisible();

    // Verify trash/recycle bin
    await filesPage.navigateToTrash();
    await expect(page.locator('[data-filename="image1.jpg"]')).toBeVisible();

    // Restore file from trash
    await filesPage.restoreFile('image1.jpg');
    await expect(page.locator('.success-message')).toContainText('File restored successfully');

    await filesPage.navigateToRoot();
    await expect(page.locator('[data-filename="image1.jpg"]')).toBeVisible();
  });

  test('dashboard and analytics workflow', async ({ page }) => {
    // Verify dashboard widgets
    await expect(dashboardPage.welcomeWidget).toBeVisible();
    await expect(dashboardPage.statsWidget).toBeVisible();
    await expect(dashboardPage.recentActivityWidget).toBeVisible();
    await expect(dashboardPage.quickActionsWidget).toBeVisible();

    // Interact with quick actions
    await dashboardPage.quickUploadFile();
    await expect(page).toHaveURL(/files\/upload/);

    await page.goBack();
    await expect(page).toHaveURL(/dashboard/);

    // View detailed analytics
    await dashboardPage.viewDetailedAnalytics();
    await expect(page).toHaveURL(/analytics/);

    // Verify analytics charts
    await expect(page.locator('[data-testid="usage-chart"]')).toBeVisible();
    await expect(page.locator('[data-testid="activity-chart"]')).toBeVisible();
    await expect(page.locator('[data-testid="storage-chart"]')).toBeVisible();

    // Change time period
    await page.click('[data-testid="time-period-selector"]');
    await page.click('[data-testid="last-30-days"]');

    // Verify charts update
    await expect(page.locator('.loading-indicator')).toBeVisible();
    await expect(page.locator('.loading-indicator')).not.toBeVisible();

    // Export analytics data
    await page.click('[data-testid="export-analytics"]');
    await page.selectOption('[data-testid="export-format"]', 'pdf');
    await page.click('[data-testid="generate-export"]');

    const downloadPromise = page.waitForEvent('download');
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('analytics');

    // Return to dashboard
    await page.click('[data-testid="back-to-dashboard"]');
    await expect(page).toHaveURL(/dashboard/);

    // Customize dashboard
    await dashboardPage.customizeDashboard();
    await expect(page.locator('.customize-modal')).toBeVisible();

    // Toggle widgets
    await page.uncheck('[data-testid="recent-activity-widget"]');
    await page.check('[data-testid="weather-widget"]');

    await page.click('[data-testid="save-customization"]');
    await expect(page.locator('.success-message')).toContainText('Dashboard customized successfully');

    // Verify widget changes
    await expect(dashboardPage.recentActivityWidget).not.toBeVisible();
    await expect(page.locator('[data-testid="weather-widget"]')).toBeVisible();

    // Reset to default layout
    await dashboardPage.customizeDashboard();
    await page.click('[data-testid="reset-to-default"]');
    await page.click('[data-testid="save-customization"]');

    await expect(dashboardPage.recentActivityWidget).toBeVisible();
    await expect(page.locator('[data-testid="weather-widget"]')).not.toBeVisible();
  });

  test('notification and communication workflow', async ({ page }) => {
    // Check notification center
    await dashboardPage.openNotificationCenter();
    await expect(page.locator('.notification-center')).toBeVisible();

    // Verify notifications are displayed
    await expect(page.locator('.notification-item')).toHaveCount.greaterThan(0);

    // Mark notification as read
    await page.click('.notification-item:first-child [data-testid="mark-read"]');
    await expect(page.locator('.notification-item:first-child')).toHaveClass(/read/);

    // Mark all as read
    await page.click('[data-testid="mark-all-read"]');
    // Verify all notifications are marked as read

    // Filter notifications
    await page.selectOption('[data-testid="notification-filter"]', 'mentions');
    // Verify only mention notifications are shown

    // Clear notifications
    await page.click('[data-testid="clear-notifications"]');
    await expect(page.locator('.confirmation-modal')).toBeVisible();
    await page.click('[data-testid="confirm-clear"]');

    await expect(page.locator('.empty-notifications')).toBeVisible();

    // Close notification center
    await page.click('[data-testid="close-notifications"]');

    // Test real-time notifications
    // This would typically involve triggering an action that generates a notification
    await dashboardPage.navigateToFiles();
    await filesPage.uploadFile('notification-test.txt');

    // Return to dashboard and check for new notification
    await dashboardPage.navigateToDashboard();
    await expect(page.locator('[data-testid="notification-badge"]')).toContainText('1');

    // Verify notification content
    await dashboardPage.openNotificationCenter();
    await expect(page.locator('.notification-item:first-child')).toContainText('File uploaded successfully');

    // Test notification settings
    await dashboardPage.navigateToProfile();
    await profilePage.navigateToNotificationsTab();

    // Disable email notifications
    await page.uncheck('[data-testid="email-notifications"]');
    await profilePage.saveNotificationSettings();

    // Enable push notifications
    await page.check('[data-testid="push-notifications"]');
    await profilePage.saveNotificationSettings();

    await expect(page.locator('.success-message')).toContainText('Notification preferences updated');
  });

  test('search and discovery workflow', async ({ page }) => {
    // Use global search
    await dashboardPage.performGlobalSearch('test');

    // Verify search results page
    await expect(page).toHaveURL(/search\?q=test/);
    await expect(page.locator('.search-results')).toBeVisible();

    // Verify different result types
    await expect(page.locator('[data-result-type="files"]')).toBeVisible();
    await expect(page.locator('[data-result-type="users"]')).toBeVisible();

    // Filter search results
    await page.click('[data-testid="files-filter"]');
    await expect(page.locator('[data-result-type="users"]')).not.toBeVisible();

    // Sort search results
    await page.selectOption('[data-testid="sort-by"]', 'relevance');
    await page.selectOption('[data-testid="sort-by"]', 'date');

    // Advanced search
    await page.click('[data-testid="advanced-search"]');
    await expect(page.locator('.advanced-search-modal')).toBeVisible();

    await page.fill('[data-testid="file-type"]', '.pdf');
    await page.fill('[data-testid="date-from"]', '2024-01-01');
    await page.selectOption('[data-testid="sort-order"]', 'desc');

    await page.click('[data-testid="apply-advanced-search"]');

    // Verify advanced search results
    await expect(page).toHaveURL(/search\?.*type=pdf/);

    // Save search
    await page.click('[data-testid="save-search"]');
    await page.fill('[data-testid="search-name"]', 'PDF Files 2024');
    await page.click('[data-testid="save-search-button"]');

    await expect(page.locator('.success-message')).toContainText('Search saved successfully');

    // Access saved searches
    await page.click('[data-testid="saved-searches"]');
    await expect(page.locator('.saved-searches-dropdown')).toBeVisible();
    await expect(page.locator('text="PDF Files 2024"')).toBeVisible();

    // Load saved search
    await page.click('text="PDF Files 2024"');
    await expect(page).toHaveURL(/search\?.*type=pdf/);

    // Delete saved search
    await page.click('[data-testid="saved-searches"]');
    await page.hover('text="PDF Files 2024"');
    await page.click('[data-testid="delete-saved-search"]');

    await expect(page.locator('.confirmation-modal')).toBeVisible();
    await page.click('[data-testid="confirm-delete"]');

    await expect(page.locator('.success-message')).toContainText('Saved search deleted');
  });
});