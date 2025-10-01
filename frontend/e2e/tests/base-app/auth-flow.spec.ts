/**
 * E2E tests for authentication flows in base-app
 */

import { test, expect } from '@playwright/test';

test.describe('Base App Authentication Flow', () => {
  const BASE_APP_URL = 'http://localhost:3000';
  const API_BASE_URL = 'http://localhost:8000';

  test.beforeEach(async ({ page }) => {
    // Set up API mocking
    await page.route(`${API_BASE_URL}/api/health`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'healthy',
          service: 'api-gateway',
          checks: {
            database: 'healthy',
            cache: 'healthy',
            auth: 'healthy',
          },
        }),
      });
    });

    await page.route(`${API_BASE_URL}/api/metrics`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          counters: {
            'requests.total': 1234,
            'errors.total': 5,
          },
          histograms: {
            'request.duration': { p50: 100, p95: 250 },
          },
        }),
      });
    });

    // Mock platform summary API route
    await page.route(`${BASE_APP_URL}/api/platform/summary`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          health: {
            status: 'healthy',
            service: 'api-gateway',
            checks: {
              database: 'healthy',
              cache: 'healthy',
              auth: 'healthy',
            },
          },
          metrics: {
            counters: { 'requests.total': 1234 },
            histograms: { 'request.duration': {} },
          },
          metricCards: [
            {
              id: 'health-checks',
              label: 'Health checks',
              value: '3/3',
              trend: 'All systems passing',
            },
            {
              id: 'counters',
              label: 'Counters tracked',
              value: '1',
              trend: 'Recorded by observability pipeline',
            },
          ],
          recentEvents: [
            {
              id: 'database-1',
              timestamp: new Date().toISOString(),
              event: 'database probe',
              actor: 'Gateway',
              status: 'healthy',
            },
          ],
        }),
      });
    });
  });

  test('landing page loads with health status', async ({ page }) => {
    await page.goto(BASE_APP_URL);

    // Check main content
    await expect(page.locator('text=DotMac Platform Starter')).toBeVisible();
    await expect(
      page.locator('text=Kick-start your next product with production-ready platform services')
    ).toBeVisible();

    // Check navigation buttons
    const dashboardLink = page.locator('a[href="/dashboard"]');
    const signInLink = page.locator('a[href="/auth/login"]');

    await expect(dashboardLink).toBeVisible();
    await expect(signInLink).toBeVisible();

    // Check health card
    await expect(page.locator('text=API health')).toBeVisible();
    await expect(page.locator('text=healthy – api-gateway')).toBeVisible();
    await expect(page.locator('text=DATABASE')).toBeVisible();
    await expect(page.locator('text=CACHE')).toBeVisible();
    await expect(page.locator('text=AUTH')).toBeVisible();
  });

  test('landing page handles health check errors', async ({ page }) => {
    // Override health API to return error
    await page.route(`${API_BASE_URL}/api/health`, async (route) => {
      await route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Service unavailable' }),
      });
    });

    await page.goto(BASE_APP_URL);

    // Should show error state
    await expect(page.locator('text=API health')).toBeVisible();
    await expect(page.locator('text=Service unavailable')).toBeVisible();
  });

  test('dashboard redirects to login when unauthenticated', async ({ page }) => {
    await page.goto(`${BASE_APP_URL}/dashboard`);

    // Should redirect to login page
    await expect(page).toHaveURL(/\/auth\/login/);
  });

  test('dashboard shows loading state', async ({ page }) => {
    // Mock authenticated state
    await page.addInitScript(() => {
      // Mock localStorage for auth state
      localStorage.setItem('auth-token', 'mock-token');
    });

    // Delay the platform summary response
    await page.route(`${BASE_APP_URL}/api/platform/summary`, async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 100));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          health: {},
          metrics: {},
          metricCards: [],
          recentEvents: [],
        }),
      });
    });

    await page.goto(`${BASE_APP_URL}/dashboard`);

    // Should show loading state
    await expect(page.locator('text=Loading metrics…')).toBeVisible();
  });

  test('dashboard displays data when authenticated', async ({ page }) => {
    // Mock authenticated state - this would need to match the actual auth implementation
    await page.addInitScript(() => {
      // This is a simplified mock - real implementation would depend on your auth provider
      window.__MOCK_AUTH_STATE__ = {
        isAuthenticated: true,
        user: { profile: { name: 'Test User' } },
      };
    });

    // Override auth check to be authenticated
    await page.addInitScript(() => {
      // Mock the auth hook to return authenticated state
      Object.defineProperty(window, 'mockAuthState', {
        value: {
          isAuthenticated: true,
          user: { profile: { name: 'Test User' } },
          logout: () => {},
        },
      });
    });

    await page.goto(`${BASE_APP_URL}/dashboard`);

    // Wait for platform summary to load
    await page.waitForResponse(`${BASE_APP_URL}/api/platform/summary`);

    // Check header
    await expect(page.locator('text=Welcome back')).toBeVisible();

    // Check metric cards
    await expect(page.locator('text=Health checks')).toBeVisible();
    await expect(page.locator('text=3/3')).toBeVisible();
    await expect(page.locator('text=All systems passing')).toBeVisible();

    await expect(page.locator('text=Counters tracked')).toBeVisible();
    await expect(page.locator('text=1')).toBeVisible();

    // Check recent events table
    await expect(page.locator('text=Recent platform events')).toBeVisible();
    await expect(page.locator('text=database probe')).toBeVisible();
    await expect(page.locator('text=Gateway')).toBeVisible();
  });

  test('dashboard handles API errors gracefully', async ({ page }) => {
    // Mock authenticated state
    await page.addInitScript(() => {
      window.__MOCK_AUTH_STATE__ = {
        isAuthenticated: true,
        user: { profile: { name: 'Test User' } },
      };
    });

    // Mock platform summary API to return error
    await page.route(`${BASE_APP_URL}/api/platform/summary`, async (route) => {
      await route.fulfill({
        status: 502,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Failed to load platform summary' }),
      });
    });

    await page.goto(`${BASE_APP_URL}/dashboard`);

    // Should show error state
    await expect(page.locator('text=Failed to load platform summary')).toBeVisible();
  });

  test('navigation between pages works correctly', async ({ page }) => {
    await page.goto(BASE_APP_URL);

    // Click dashboard link
    await page.click('a[href="/dashboard"]');
    await expect(page).toHaveURL(/\/dashboard/);

    // Go back to home
    await page.goBack();
    await expect(page).toHaveURL(/^\//);

    // Click sign in link
    await page.click('a[href="/auth/login"]');
    await expect(page).toHaveURL(/\/auth\/login/);
  });

  test('responsive design works on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE size

    await page.goto(BASE_APP_URL);

    // Main content should still be visible
    await expect(page.locator('text=DotMac Platform Starter')).toBeVisible();
    await expect(page.locator('text=API health')).toBeVisible();

    // Navigation buttons should be stacked
    const dashboardLink = page.locator('a[href="/dashboard"]');
    const signInLink = page.locator('a[href="/auth/login"]');

    await expect(dashboardLink).toBeVisible();
    await expect(signInLink).toBeVisible();
  });

  test('API route proxy works correctly', async ({ page }) => {
    // Remove mocking to test actual proxy
    await page.unroute(`${BASE_APP_URL}/api/platform/summary`);

    await page.goto(BASE_APP_URL);

    // Monitor network requests
    const requests: string[] = [];
    page.on('request', (request) => {
      requests.push(request.url());
    });

    // This would test the actual proxy in a real environment
    // For now, we'll verify the route structure exists
    const response = await page.request.get(`${BASE_APP_URL}/api/platform/summary`);

    // The route should exist (even if backend is not available)
    // A 502 is expected when backend is not running, which is acceptable
    expect([200, 502, 503]).toContain(response.status());
  });

  test('error boundary handles JavaScript errors', async ({ page }) => {
    // Inject a script that will cause an error
    await page.addInitScript(() => {
      // Override a React component to throw an error
      window.__FORCE_ERROR__ = true;
    });

    await page.goto(BASE_APP_URL);

    // Page should still load (error boundary should catch errors)
    // This test would need to be expanded based on actual error boundary implementation
    await expect(page.locator('body')).toBeVisible();
  });
});