import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';
import { MFAPage } from '../pages/MFAPage';
import { DashboardPage } from '../pages/DashboardPage';
import { generateTOTP } from '../utils/totp-helper';

test.describe('Multi-Factor Authentication', () => {
  let loginPage: LoginPage;
  let mfaPage: MFAPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    mfaPage = new MFAPage(page);
    dashboardPage = new DashboardPage(page);
    await loginPage.goto();
  });

  test('should setup MFA for new user', async ({ page }) => {
    // Login as regular user (assuming MFA not setup yet)
    await loginPage.login('user@test.com', 'Test123!@#');

    // Should redirect to MFA setup
    await expect(page).toHaveURL(/mfa\/setup/);
    await expect(mfaPage.setupTitle).toContainText('Set up Two-Factor Authentication');

    // Should display QR code
    await expect(mfaPage.qrCode).toBeVisible();

    // Should display manual entry key
    await expect(mfaPage.manualEntryKey).toBeVisible();
    const secretKey = await mfaPage.manualEntryKey.textContent();
    expect(secretKey).toBeTruthy();

    // Enter TOTP code
    const totpCode = generateTOTP(secretKey!);
    await mfaPage.fillTOTPCode(totpCode);
    await mfaPage.verifyButton.click();

    // Should complete setup and redirect to dashboard
    await expect(page).toHaveURL(/dashboard/);
    await expect(dashboardPage.mfaEnabledBadge).toBeVisible();
  });

  test('should require MFA code after initial login', async ({ page }) => {
    // Assuming user already has MFA setup
    await loginPage.login('admin@test.com', 'Test123!@#');

    // Should redirect to MFA verification
    await expect(page).toHaveURL(/mfa\/verify/);
    await expect(mfaPage.verificationTitle).toContainText('Enter Authentication Code');

    // Should show TOTP input
    await expect(mfaPage.totpInput).toBeVisible();
    await expect(mfaPage.verifyButton).toBeVisible();
  });

  test('should login successfully with valid TOTP code', async ({ page }) => {
    await loginPage.login('admin@test.com', 'Test123!@#');
    await expect(page).toHaveURL(/mfa\/verify/);

    // Get the secret from user's MFA setup (in real test, this would be stored)
    const secretKey = 'JBSWY3DPEHPK3PXP'; // Example secret
    const totpCode = generateTOTP(secretKey);

    await mfaPage.fillTOTPCode(totpCode);
    await mfaPage.verifyButton.click();

    // Should redirect to dashboard
    await expect(page).toHaveURL(/dashboard/);
    await expect(dashboardPage.welcomeMessage).toBeVisible();
  });

  test('should reject invalid TOTP code', async ({ page }) => {
    await loginPage.login('admin@test.com', 'Test123!@#');
    await expect(page).toHaveURL(/mfa\/verify/);

    // Enter invalid code
    await mfaPage.fillTOTPCode('000000');
    await mfaPage.verifyButton.click();

    // Should show error and stay on MFA page
    await expect(page).toHaveURL(/mfa\/verify/);
    await expect(mfaPage.errorMessage).toBeVisible();
    await expect(mfaPage.errorMessage).toContainText('Invalid authentication code');
  });

  test('should handle expired TOTP codes', async ({ page }) => {
    await loginPage.login('admin@test.com', 'Test123!@#');
    await expect(page).toHaveURL(/mfa\/verify/);

    // Use an old/expired code (simulate by using wrong timestamp)
    const expiredCode = generateTOTP('JBSWY3DPEHPK3PXP', Date.now() - 180000); // 3 minutes ago

    await mfaPage.fillTOTPCode(expiredCode);
    await mfaPage.verifyButton.click();

    await expect(mfaPage.errorMessage).toContainText('Authentication code has expired');
  });

  test('should provide backup codes option', async ({ page }) => {
    await loginPage.login('admin@test.com', 'Test123!@#');
    await expect(page).toHaveURL(/mfa\/verify/);

    // Click "Use backup code" link
    await mfaPage.useBackupCodeLink.click();

    // Should show backup code input
    await expect(mfaPage.backupCodeInput).toBeVisible();
    await expect(mfaPage.backupCodeTitle).toContainText('Enter Backup Code');
  });

  test('should login with valid backup code', async ({ page }) => {
    await loginPage.login('admin@test.com', 'Test123!@#');
    await mfaPage.useBackupCodeLink.click();

    // Use a pre-generated backup code (in real scenario, from user's account)
    const backupCode = 'ABC123DEF456';
    await mfaPage.fillBackupCode(backupCode);
    await mfaPage.verifyBackupCodeButton.click();

    // Should redirect to dashboard
    await expect(page).toHaveURL(/dashboard/);

    // Should show warning about backup code usage
    await expect(dashboardPage.backupCodeUsedAlert).toBeVisible();
  });

  test('should reject used backup code', async ({ page }) => {
    await loginPage.login('admin@test.com', 'Test123!@#');
    await mfaPage.useBackupCodeLink.click();

    // Use already used backup code
    const usedBackupCode = 'USED123CODE456';
    await mfaPage.fillBackupCode(usedBackupCode);
    await mfaPage.verifyBackupCodeButton.click();

    await expect(mfaPage.errorMessage).toContainText('Backup code has already been used');
  });

  test('should rate limit MFA attempts', async ({ page }) => {
    await loginPage.login('admin@test.com', 'Test123!@#');
    await expect(page).toHaveURL(/mfa\/verify/);

    // Make multiple failed attempts
    for (let i = 0; i < 5; i++) {
      await mfaPage.fillTOTPCode('000000');
      await mfaPage.verifyButton.click();
      await expect(mfaPage.errorMessage).toBeVisible();
    }

    // Next attempt should be rate limited
    await mfaPage.fillTOTPCode('000000');
    await mfaPage.verifyButton.click();

    await expect(mfaPage.errorMessage).toContainText('Too many failed attempts');
    await expect(mfaPage.totpInput).toBeDisabled();
  });

  test('should allow MFA disable from settings', async ({ page }) => {
    // Login and go to settings
    await loginPage.login('admin@test.com', 'Test123!@#');
    // Skip MFA verification for this test (use session token directly)
    await page.goto('/settings/security');

    // Should show MFA status as enabled
    await expect(page.locator('[data-testid="mfa-status"]')).toContainText('Enabled');

    // Click disable MFA
    await page.locator('[data-testid="disable-mfa-button"]').click();

    // Should require password confirmation
    await expect(page.locator('[data-testid="confirm-password-modal"]')).toBeVisible();
    await page.locator('[data-testid="password-input"]').fill('Test123!@#');
    await page.locator('[data-testid="confirm-disable-button"]').click();

    // Should show MFA as disabled
    await expect(page.locator('[data-testid="mfa-status"]')).toContainText('Disabled');

    // Should generate new backup codes
    await expect(page.locator('[data-testid="new-backup-codes"]')).toBeVisible();
  });

  test('should handle lost device recovery', async ({ page }) => {
    await loginPage.login('admin@test.com', 'Test123!@#');
    await expect(page).toHaveURL(/mfa\/verify/);

    // Click "Lost your device?" link
    await mfaPage.lostDeviceLink.click();

    // Should redirect to recovery page
    await expect(page).toHaveURL(/mfa\/recovery/);
    await expect(page.locator('h1')).toContainText('Account Recovery');

    // Should show recovery options
    await expect(page.locator('[data-testid="email-recovery"]')).toBeVisible();
    await expect(page.locator('[data-testid="sms-recovery"]')).toBeVisible();
    await expect(page.locator('[data-testid="support-contact"]')).toBeVisible();
  });

  test('should show TOTP code format validation', async ({ page }) => {
    await loginPage.login('admin@test.com', 'Test123!@#');
    await expect(page).toHaveURL(/mfa\/verify/);

    // Test invalid format inputs
    await mfaPage.fillTOTPCode('123'); // Too short
    await expect(mfaPage.formatError).toContainText('Code must be 6 digits');

    await mfaPage.fillTOTPCode('abcdef'); // Non-numeric
    await expect(mfaPage.formatError).toContainText('Code must contain only numbers');

    await mfaPage.fillTOTPCode('1234567'); // Too long
    await expect(mfaPage.formatError).toContainText('Code must be exactly 6 digits');
  });

  test('should auto-submit when 6 digits entered', async ({ page }) => {
    await loginPage.login('admin@test.com', 'Test123!@#');
    await expect(page).toHaveURL(/mfa\/verify/);

    const secretKey = 'JBSWY3DPEHPK3PXP';
    const totpCode = generateTOTP(secretKey);

    // Fill code character by character
    for (let i = 0; i < totpCode.length; i++) {
      await mfaPage.totpInput.fill(totpCode.substring(0, i + 1));
    }

    // Should auto-submit when 6th digit is entered
    await expect(page).toHaveURL(/dashboard/);
  });

  test('should remember device option', async ({ page, context }) => {
    await loginPage.login('admin@test.com', 'Test123!@#');
    await expect(page).toHaveURL(/mfa\/verify/);

    // Check "Remember this device"
    await mfaPage.rememberDeviceCheckbox.check();

    const secretKey = 'JBSWY3DPEHPK3PXP';
    const totpCode = generateTOTP(secretKey);
    await mfaPage.fillTOTPCode(totpCode);
    await mfaPage.verifyButton.click();

    // Should set remember device cookie
    const cookies = await context.cookies();
    const rememberDeviceCookie = cookies.find(cookie => cookie.name === 'remember_device');
    expect(rememberDeviceCookie).toBeDefined();

    // Future logins should skip MFA
    await dashboardPage.logout();
    await loginPage.login('admin@test.com', 'Test123!@#');

    // Should go directly to dashboard (skip MFA)
    await expect(page).toHaveURL(/dashboard/);
  });
});