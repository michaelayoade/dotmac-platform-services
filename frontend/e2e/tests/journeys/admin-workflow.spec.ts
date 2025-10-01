import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';
import { UserManagementPage } from '../pages/UserManagementPage';
import { FeatureFlagsPage } from '../pages/FeatureFlagsPage';

test.describe('Admin User Journey', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;
  let userManagementPage: UserManagementPage;
  let featureFlagsPage: FeatureFlagsPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    userManagementPage = new UserManagementPage(page);
    featureFlagsPage = new FeatureFlagsPage(page);

    // Login as admin
    await loginPage.goto();
    await loginPage.login('admin@test.com', 'Test123!@#');
    await expect(page).toHaveURL(/dashboard/);
  });

  test('complete user management workflow', async ({ page }) => {
    // Navigate to user management
    await dashboardPage.navigateToUserManagement();
    await expect(page).toHaveURL(/admin\/users/);

    // Create new user
    await userManagementPage.clickCreateUser();
    await expect(page).toHaveURL(/admin\/users\/create/);

    const newUser = {
      email: 'journey-user@test.com',
      fullName: 'Journey Test User',
      username: 'journeyuser',
      password: 'Test123!@#',
      role: 'user'
    };

    await userManagementPage.fillUserForm(newUser);
    await userManagementPage.submitForm();

    // Verify user creation success
    await expect(page.locator('.success-message')).toContainText('User created successfully');
    await expect(page).toHaveURL(/admin\/users/);

    // Search for the created user
    await userManagementPage.searchUsers(newUser.email);
    await expect(userManagementPage.userRow(newUser.email)).toBeVisible();

    // Edit the user
    await userManagementPage.editUser(newUser.email);
    await expect(page).toHaveURL(/admin\/users\/\d+\/edit/);

    // Update user details
    await userManagementPage.updateUserField('fullName', 'Updated Journey User');
    await userManagementPage.addRole('admin');
    await userManagementPage.submitForm();

    // Verify update success
    await expect(page.locator('.success-message')).toContainText('User updated successfully');
    await expect(page).toHaveURL(/admin\/users/);

    // Verify changes in user list
    await userManagementPage.searchUsers(newUser.email);
    await expect(userManagementPage.userRow(newUser.email)).toContainText('Updated Journey User');
    await expect(userManagementPage.userRow(newUser.email)).toContainText('admin');

    // View user details
    await userManagementPage.viewUserDetails(newUser.email);
    await expect(page).toHaveURL(/admin\/users\/\d+/);

    // Verify all user information is displayed correctly
    await expect(page.locator('[data-testid="user-email"]')).toContainText(newUser.email);
    await expect(page.locator('[data-testid="user-name"]')).toContainText('Updated Journey User');
    await expect(page.locator('[data-testid="user-roles"]')).toContainText('admin');
    await expect(page.locator('[data-testid="user-roles"]')).toContainText('user');

    // Check user activity log
    await expect(page.locator('[data-testid="activity-log"]')).toBeVisible();
    await expect(page.locator('[data-testid="activity-log"]')).toContainText('User created');
    await expect(page.locator('[data-testid="activity-log"]')).toContainText('User updated');

    // Return to user list
    await page.click('[data-testid="back-to-users"]');
    await expect(page).toHaveURL(/admin\/users/);

    // Deactivate user
    await userManagementPage.searchUsers(newUser.email);
    await userManagementPage.deactivateUser(newUser.email);

    // Confirm deactivation in modal
    await expect(page.locator('.confirmation-modal')).toBeVisible();
    await page.click('[data-testid="confirm-deactivate"]');

    // Verify deactivation
    await expect(page.locator('.success-message')).toContainText('User deactivated successfully');
    await expect(userManagementPage.userRow(newUser.email)).toHaveClass(/deactivated/);

    // Reactivate user
    await userManagementPage.reactivateUser(newUser.email);
    await expect(page.locator('.success-message')).toContainText('User reactivated successfully');
    await expect(userManagementPage.userRow(newUser.email)).not.toHaveClass(/deactivated/);
  });

  test('feature flag management workflow', async ({ page }) => {
    // Navigate to feature flags
    await dashboardPage.navigateToFeatureFlags();
    await expect(page).toHaveURL(/admin\/feature-flags/);

    // Create new feature flag
    await featureFlagsPage.clickCreateFlag();
    await expect(page).toHaveURL(/admin\/feature-flags\/create/);

    const newFlag = {
      key: 'journey-test-feature',
      name: 'Journey Test Feature',
      description: 'A test feature for E2E testing',
      strategy: 'percentage',
      percentage: 0
    };

    await featureFlagsPage.fillFlagForm(newFlag);
    await featureFlagsPage.submitForm();

    // Verify flag creation
    await expect(page.locator('.success-message')).toContainText('Feature flag created successfully');
    await expect(page).toHaveURL(/admin\/feature-flags/);

    // Verify flag appears in list
    await expect(featureFlagsPage.flagRow(newFlag.key)).toBeVisible();
    await expect(featureFlagsPage.flagRow(newFlag.key)).toContainText(newFlag.name);
    await expect(featureFlagsPage.flagStatus(newFlag.key)).toContainText('0%');

    // Enable flag with 50% rollout
    await featureFlagsPage.editFlag(newFlag.key);
    await featureFlagsPage.updatePercentage(50);
    await featureFlagsPage.submitForm();

    // Verify update
    await expect(page.locator('.success-message')).toContainText('Feature flag updated successfully');
    await expect(featureFlagsPage.flagStatus(newFlag.key)).toContainText('50%');

    // Test flag evaluation
    await featureFlagsPage.testFlag(newFlag.key);
    await expect(page.locator('.flag-test-results')).toBeVisible();

    // Add user targeting
    await featureFlagsPage.editFlag(newFlag.key);
    await featureFlagsPage.addUserTarget('journey-user@test.com');
    await featureFlagsPage.submitForm();

    // Verify targeting
    await expect(featureFlagsPage.flagTargets(newFlag.key)).toContainText('journey-user@test.com');

    // Set flag to 100% enabled
    await featureFlagsPage.quickToggle(newFlag.key, 100);
    await expect(featureFlagsPage.flagStatus(newFlag.key)).toContainText('100%');

    // Archive the flag
    await featureFlagsPage.archiveFlag(newFlag.key);
    await expect(page.locator('.confirmation-modal')).toBeVisible();
    await page.click('[data-testid="confirm-archive"]');

    // Verify archival
    await expect(page.locator('.success-message')).toContainText('Feature flag archived');

    // Flag should be moved to archived section
    await featureFlagsPage.showArchivedFlags();
    await expect(featureFlagsPage.archivedFlagRow(newFlag.key)).toBeVisible();
  });

  test('system monitoring and analytics workflow', async ({ page }) => {
    // Navigate to system monitoring
    await dashboardPage.navigateToMonitoring();
    await expect(page).toHaveURL(/admin\/monitoring/);

    // Verify system health indicators
    await expect(page.locator('[data-testid="system-health"]')).toBeVisible();
    await expect(page.locator('[data-testid="api-status"]')).toContainText('Healthy');
    await expect(page.locator('[data-testid="database-status"]')).toContainText('Connected');
    await expect(page.locator('[data-testid="cache-status"]')).toContainText('Online');

    // Check performance metrics
    await expect(page.locator('[data-testid="response-time-chart"]')).toBeVisible();
    await expect(page.locator('[data-testid="throughput-chart"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-rate-chart"]')).toBeVisible();

    // Navigate to user analytics
    await page.click('[data-testid="user-analytics-tab"]');

    // Verify user metrics
    await expect(page.locator('[data-testid="active-users"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-growth-chart"]')).toBeVisible();
    await expect(page.locator('[data-testid="user-activity-table"]')).toBeVisible();

    // Filter analytics by date range
    await page.click('[data-testid="date-range-picker"]');
    await page.click('[data-testid="last-7-days"]');

    // Verify charts update
    await expect(page.locator('[data-testid="loading-indicator"]')).toBeVisible();
    await expect(page.locator('[data-testid="loading-indicator"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="date-range-label"]')).toContainText('Last 7 days');

    // Export analytics data
    await page.click('[data-testid="export-data"]');
    await page.click('[data-testid="export-csv"]');

    // Verify download initiated
    const downloadPromise = page.waitForEvent('download');
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('analytics');
    expect(download.suggestedFilename()).toContain('.csv');

    // Navigate to alerts
    await page.click('[data-testid="alerts-tab"]');

    // Verify alerts section
    await expect(page.locator('[data-testid="active-alerts"]')).toBeVisible();
    await expect(page.locator('[data-testid="alert-history"]')).toBeVisible();

    // Create a new alert rule
    await page.click('[data-testid="create-alert"]');
    await expect(page.locator('.alert-modal')).toBeVisible();

    await page.fill('[data-testid="alert-name"]', 'High Error Rate Alert');
    await page.selectOption('[data-testid="alert-metric"]', 'error_rate');
    await page.fill('[data-testid="alert-threshold"]', '5');
    await page.selectOption('[data-testid="alert-condition"]', 'greater_than');
    await page.click('[data-testid="save-alert"]');

    // Verify alert creation
    await expect(page.locator('.success-message')).toContainText('Alert rule created');
    await expect(page.locator('[data-testid="alert-rules"]')).toContainText('High Error Rate Alert');
  });

  test('complete admin settings workflow', async ({ page }) => {
    // Navigate to admin settings
    await dashboardPage.navigateToSettings();
    await expect(page).toHaveURL(/admin\/settings/);

    // Update general settings
    await page.click('[data-testid="general-settings-tab"]');
    await page.fill('[data-testid="site-name"]', 'DotMac E2E Test Site');
    await page.fill('[data-testid="admin-email"]', 'admin-test@dotmac.com');
    await page.click('[data-testid="save-general-settings"]');

    await expect(page.locator('.success-message')).toContainText('Settings saved successfully');

    // Configure security settings
    await page.click('[data-testid="security-settings-tab"]');

    // Enable MFA requirement
    await page.check('[data-testid="require-mfa"]');

    // Set password policy
    await page.fill('[data-testid="min-password-length"]', '12');
    await page.check('[data-testid="require-special-chars"]');
    await page.fill('[data-testid="session-timeout"]', '60');

    await page.click('[data-testid="save-security-settings"]');
    await expect(page.locator('.success-message')).toContainText('Security settings updated');

    // Configure email settings
    await page.click('[data-testid="email-settings-tab"]');
    await page.fill('[data-testid="smtp-host"]', 'smtp.test.com');
    await page.fill('[data-testid="smtp-port"]', '587');
    await page.fill('[data-testid="smtp-username"]', 'test@dotmac.com');

    // Test email configuration
    await page.click('[data-testid="test-email"]');
    await page.fill('[data-testid="test-email-recipient"]', 'admin@test.com');
    await page.click('[data-testid="send-test-email"]');

    await expect(page.locator('.info-message')).toContainText('Test email sent');

    // Configure API settings
    await page.click('[data-testid="api-settings-tab"]');

    // Set rate limits
    await page.fill('[data-testid="rate-limit-requests"]', '1000');
    await page.fill('[data-testid="rate-limit-window"]', '60');

    // Enable API logging
    await page.check('[data-testid="enable-api-logging"]');

    // Configure CORS
    await page.fill('[data-testid="cors-origins"]', 'https://app.dotmac.com, https://admin.dotmac.com');

    await page.click('[data-testid="save-api-settings"]');
    await expect(page.locator('.success-message')).toContainText('API settings updated');

    // Backup and restore
    await page.click('[data-testid="backup-restore-tab"]');

    // Create backup
    await page.click('[data-testid="create-backup"]');
    await expect(page.locator('.info-message')).toContainText('Backup created successfully');

    // Verify backup appears in list
    await expect(page.locator('[data-testid="backup-list"]')).toContainText('backup-');

    // Schedule automatic backups
    await page.check('[data-testid="enable-auto-backup"]');
    await page.selectOption('[data-testid="backup-frequency"]', 'daily');
    await page.fill('[data-testid="backup-retention"]', '30');

    await page.click('[data-testid="save-backup-settings"]');
    await expect(page.locator('.success-message')).toContainText('Backup settings saved');

    // System maintenance
    await page.click('[data-testid="maintenance-tab"]');

    // Clear cache
    await page.click('[data-testid="clear-cache"]');
    await expect(page.locator('.success-message')).toContainText('Cache cleared successfully');

    // Rebuild search index
    await page.click('[data-testid="rebuild-search-index"]');
    await expect(page.locator('.info-message')).toContainText('Search index rebuild started');

    // Schedule maintenance mode
    await page.check('[data-testid="enable-maintenance-mode"]');
    await page.fill('[data-testid="maintenance-message"]', 'System maintenance in progress');
    await page.click('[data-testid="save-maintenance-settings"]');

    await expect(page.locator('.warning-message')).toContainText('Maintenance mode enabled');

    // Disable maintenance mode
    await page.uncheck('[data-testid="enable-maintenance-mode"]');
    await page.click('[data-testid="save-maintenance-settings"]');

    await expect(page.locator('.success-message')).toContainText('Maintenance mode disabled');
  });

  test('audit trail and compliance workflow', async ({ page }) => {
    // Navigate to audit trail
    await dashboardPage.navigateToAuditTrail();
    await expect(page).toHaveURL(/admin\/audit/);

    // Verify audit events are displayed
    await expect(page.locator('[data-testid="audit-events"]')).toBeVisible();
    await expect(page.locator('[data-testid="event-count"]')).toBeVisible();

    // Filter audit events
    await page.selectOption('[data-testid="event-type-filter"]', 'user_login');
    await page.click('[data-testid="apply-filter"]');

    // Verify filtered results
    await expect(page.locator('.audit-event')).toContainText('User Login');

    // Search by user
    await page.fill('[data-testid="user-search"]', 'admin@test.com');
    await page.click('[data-testid="search-button"]');

    // Verify search results
    await expect(page.locator('.audit-event')).toContainText('admin@test.com');

    // View event details
    await page.click('.audit-event:first-child [data-testid="view-details"]');
    await expect(page.locator('.event-details-modal')).toBeVisible();

    // Verify event details
    await expect(page.locator('[data-testid="event-timestamp"]')).toBeVisible();
    await expect(page.locator('[data-testid="event-user"]')).toBeVisible();
    await expect(page.locator('[data-testid="event-ip"]')).toBeVisible();
    await expect(page.locator('[data-testid="event-user-agent"]')).toBeVisible();

    await page.click('[data-testid="close-details"]');

    // Export audit report
    await page.click('[data-testid="export-audit"]');
    await page.selectOption('[data-testid="export-format"]', 'pdf');
    await page.click('[data-testid="generate-report"]');

    // Wait for report generation
    await expect(page.locator('.report-progress')).toBeVisible();
    await expect(page.locator('.report-progress')).not.toBeVisible();

    // Verify download
    const downloadPromise = page.waitForEvent('download');
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('audit-report');
    expect(download.suggestedFilename()).toContain('.pdf');

    // Configure audit retention
    await page.click('[data-testid="audit-settings"]');
    await expect(page.locator('.audit-settings-modal')).toBeVisible();

    await page.fill('[data-testid="retention-days"]', '365');
    await page.check('[data-testid="log-api-calls"]');
    await page.check('[data-testid="log-file-access"]');
    await page.click('[data-testid="save-audit-settings"]');

    await expect(page.locator('.success-message')).toContainText('Audit settings updated');
  });
});