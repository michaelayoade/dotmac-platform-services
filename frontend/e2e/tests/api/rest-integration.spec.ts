import { test, expect } from '@playwright/test';
import { APITestHelper } from '../utils/api-helper';

test.describe('REST API Integration', () => {
  let apiHelper: APITestHelper;

  test.beforeEach(async ({ page }) => {
    apiHelper = new APITestHelper(page);
    await apiHelper.authenticate('admin@test.com', 'Test123!@#');
  });

  test.describe('User Management API', () => {
    test('should create user via API and reflect in UI', async ({ page }) => {
      // Create user via API
      const newUser = {
        email: 'newuser@test.com',
        username: 'newuser',
        full_name: 'New Test User',
        password: 'Test123!@#',
        roles: ['user']
      };

      const createResponse = await apiHelper.createUser(newUser);
      expect(createResponse.status()).toBe(201);

      const userData = await createResponse.json();
      expect(userData.email).toBe(newUser.email);

      // Navigate to users page
      await page.goto('/admin/users');

      // Verify user appears in UI
      await expect(page.locator(`[data-user-id="${userData.id}"]`)).toBeVisible();
      await expect(page.locator(`text=${newUser.full_name}`)).toBeVisible();
    });

    test('should update user via API and reflect in UI', async ({ page }) => {
      // First create a user
      const user = await apiHelper.createTestUser();
      const userId = user.id;

      // Navigate to user edit page
      await page.goto(`/admin/users/${userId}/edit`);

      // Update via API
      const updatedData = { full_name: 'Updated User Name' };
      const updateResponse = await apiHelper.updateUser(userId, updatedData);
      expect(updateResponse.status()).toBe(200);

      // Refresh page and verify update
      await page.reload();
      await expect(page.locator('input[name="full_name"]')).toHaveValue('Updated User Name');
    });

    test('should delete user via API and remove from UI', async ({ page }) => {
      // Create user and navigate to users list
      const user = await apiHelper.createTestUser();
      await page.goto('/admin/users');

      // Verify user exists in UI
      await expect(page.locator(`[data-user-id="${user.id}"]`)).toBeVisible();

      // Delete via API
      const deleteResponse = await apiHelper.deleteUser(user.id);
      expect(deleteResponse.status()).toBe(204);

      // Refresh and verify user is gone
      await page.reload();
      await expect(page.locator(`[data-user-id="${user.id}"]`)).not.toBeVisible();
    });

    test('should handle API errors gracefully in UI', async ({ page }) => {
      await page.goto('/admin/users/create');

      // Intercept API call to return error
      await page.route('**/api/users', route => {
        route.fulfill({
          status: 422,
          contentType: 'application/json',
          body: JSON.stringify({
            error: {
              code: 'VALIDATION_FAILED',
              message: 'Validation failed',
              details: {
                email: 'Email already exists'
              }
            }
          })
        });
      });

      // Fill form and submit
      await page.fill('input[name="email"]', 'existing@test.com');
      await page.fill('input[name="full_name"]', 'Test User');
      await page.fill('input[name="password"]', 'Test123!@#');
      await page.click('button[type="submit"]');

      // Verify error display
      await expect(page.locator('.error-message')).toContainText('Email already exists');
      await expect(page.locator('input[name="email"]')).toHaveClass(/error/);
    });
  });

  test.describe('Feature Flags API', () => {
    test('should toggle feature flag and reflect in UI', async ({ page }) => {
      // Create a feature flag
      const flagData = {
        key: 'new-dashboard',
        name: 'New Dashboard',
        description: 'Enable new dashboard interface',
        strategy: 'percentage',
        percentage: 0
      };

      const createResponse = await apiHelper.createFeatureFlag(flagData);
      expect(createResponse.status()).toBe(201);

      const flag = await createResponse.json();

      // Navigate to feature flags page
      await page.goto('/admin/feature-flags');
      await expect(page.locator(`[data-flag-key="${flag.key}"]`)).toBeVisible();

      // Toggle flag via API
      const toggleResponse = await apiHelper.toggleFeatureFlag(flag.key, { percentage: 100 });
      expect(toggleResponse.status()).toBe(200);

      // Refresh and verify toggle state
      await page.reload();
      await expect(page.locator(`[data-flag-key="${flag.key}"] .toggle-switch`)).toBeChecked();
    });

    test('should evaluate feature flag in real-time', async ({ page }) => {
      // Enable a feature flag that affects UI
      await apiHelper.createFeatureFlag({
        key: 'beta-features',
        name: 'Beta Features',
        strategy: 'percentage',
        percentage: 100
      });

      // Navigate to page that uses the flag
      await page.goto('/dashboard');

      // Verify beta features are visible
      await expect(page.locator('[data-testid="beta-feature"]')).toBeVisible();

      // Disable the flag
      await apiHelper.toggleFeatureFlag('beta-features', { percentage: 0 });

      // Refresh page - beta features should be hidden
      await page.reload();
      await expect(page.locator('[data-testid="beta-feature"]')).not.toBeVisible();
    });
  });

  test.describe('File Upload API', () => {
    test('should upload file via API and display in UI', async ({ page }) => {
      // Create a test file
      const fileContent = 'Test file content for E2E testing';
      const uploadResponse = await apiHelper.uploadFile('test.txt', fileContent);
      expect(uploadResponse.status()).toBe(201);

      const fileData = await uploadResponse.json();

      // Navigate to files page
      await page.goto('/files');

      // Verify file appears in UI
      await expect(page.locator(`[data-file-id="${fileData.id}"]`)).toBeVisible();
      await expect(page.locator(`text=test.txt`)).toBeVisible();
    });

    test('should handle file upload progress', async ({ page }) => {
      await page.goto('/files/upload');

      // Intercept upload request to simulate progress
      let progressCallback: Function;
      await page.route('**/api/files/upload', route => {
        // Simulate upload progress
        progressCallback = (progress: number) => {
          page.evaluate((p) => {
            window.dispatchEvent(new CustomEvent('upload-progress', { detail: { progress: p } }));
          }, progress);
        };

        setTimeout(() => {
          progressCallback(25);
          setTimeout(() => {
            progressCallback(50);
            setTimeout(() => {
              progressCallback(75);
              setTimeout(() => {
                progressCallback(100);
                route.fulfill({
                  status: 201,
                  contentType: 'application/json',
                  body: JSON.stringify({ id: 'file123', name: 'test.txt' })
                });
              }, 500);
            }, 500);
          }, 500);
        }, 500);
      });

      // Upload file
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: 'test.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('Test content')
      });

      // Verify progress bar
      await expect(page.locator('.progress-bar')).toBeVisible();
      await expect(page.locator('.progress-bar')).toHaveAttribute('value', '100');
      await expect(page.locator('.upload-complete')).toBeVisible();
    });
  });

  test.describe('Real-time Updates', () => {
    test('should receive WebSocket notifications', async ({ page }) => {
      await page.goto('/dashboard');

      // Listen for WebSocket messages
      const webSocketPromise = page.waitForEvent('websocket');

      // Trigger an action that should send a notification
      await apiHelper.createUser({
        email: 'realtime@test.com',
        username: 'realtime',
        full_name: 'Realtime User',
        password: 'Test123!@#'
      });

      const webSocket = await webSocketPromise;

      // Wait for WebSocket message
      const messagePromise = new Promise((resolve) => {
        webSocket.on('framereceived', (frame) => {
          const data = JSON.parse(frame.payload.toString());
          if (data.type === 'user_created') {
            resolve(data);
          }
        });
      });

      const message = await messagePromise;
      expect(message).toHaveProperty('type', 'user_created');

      // Verify notification appears in UI
      await expect(page.locator('.notification')).toContainText('New user created');
    });

    test('should handle WebSocket reconnection', async ({ page }) => {
      await page.goto('/dashboard');

      // Wait for initial WebSocket connection
      await page.waitForEvent('websocket');

      // Simulate network disconnection
      await page.context().setOffline(true);

      // Wait a moment
      await page.waitForTimeout(1000);

      // Restore connection
      await page.context().setOffline(false);

      // Verify reconnection indicator
      await expect(page.locator('.connection-status')).toContainText('Connected');
    });
  });

  test.describe('API Error Handling', () => {
    test('should handle 500 errors gracefully', async ({ page }) => {
      await page.goto('/dashboard');

      // Intercept API calls to return 500 error
      await page.route('**/api/**', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            error: {
              code: 'INTERNAL_SERVER_ERROR',
              message: 'Internal server error'
            }
          })
        });
      });

      // Try to perform an action
      await page.click('[data-testid="refresh-data"]');

      // Verify error handling
      await expect(page.locator('.error-banner')).toBeVisible();
      await expect(page.locator('.error-banner')).toContainText('Something went wrong');
    });

    test('should handle network timeouts', async ({ page }) => {
      await page.goto('/dashboard');

      // Intercept API calls and delay indefinitely
      await page.route('**/api/users', route => {
        // Never resolve to simulate timeout
      });

      // Set shorter timeout for testing
      await page.evaluate(() => {
        window.fetch = new Proxy(window.fetch, {
          apply: (target, thisArg, args) => {
            const [url, options = {}] = args;
            options.timeout = 5000; // 5 second timeout
            return target.apply(thisArg, [url, options]);
          }
        });
      });

      // Try to load data
      await page.click('[data-testid="load-users"]');

      // Verify timeout handling
      await expect(page.locator('.timeout-error')).toBeVisible();
      await expect(page.locator('.retry-button')).toBeVisible();
    });

    test('should retry failed requests', async ({ page }) => {
      await page.goto('/dashboard');

      let attemptCount = 0;
      await page.route('**/api/users', route => {
        attemptCount++;
        if (attemptCount < 3) {
          // Fail first 2 attempts
          route.fulfill({
            status: 503,
            contentType: 'application/json',
            body: JSON.stringify({ error: { code: 'SERVICE_UNAVAILABLE', message: 'Service temporarily unavailable' } })
          });
        } else {
          // Succeed on 3rd attempt
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify([{ id: 1, name: 'Test User' }])
          });
        }
      });

      await page.click('[data-testid="load-users"]');

      // Verify retry mechanism worked
      await expect(page.locator('[data-testid="users-list"]')).toBeVisible();
      expect(attemptCount).toBe(3);
    });
  });
});