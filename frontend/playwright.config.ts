import { defineConfig, devices } from "@playwright/test";
import path from "path";

const baseURL = process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e/tests",

  // Global setup/teardown for authentication
  globalSetup: "./e2e/global-setup.ts",
  globalTeardown: "./e2e/global-teardown.ts",

  // Run tests in parallel across files
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Limit workers on CI to avoid overloading
  workers: process.env.CI ? 4 : undefined,

  // Reporter configuration
  reporter: [
    ["html", { outputFolder: "playwright/test-results/html" }],
    ["json", { outputFile: "playwright/test-results/results.json" }],
    ["junit", { outputFile: "playwright/test-results/junit.xml" }],
    process.env.CI ? ["github"] : ["list"],
  ],

  // Shared settings for all projects
  use: {
    baseURL,

    // Collect trace on first retry
    trace: "on-first-retry",

    // Screenshot on failure
    screenshot: "only-on-failure",

    // Video on failure
    video: "on-first-retry",

    // Action timeout
    actionTimeout: 10000,

    // Navigation timeout
    navigationTimeout: 30000,
  },

  // Configure projects for different test categories
  projects: [
    // Smoke tests - critical path only (fast)
    {
      name: "smoke",
      testMatch: /.*\.smoke\.spec\.ts/,
      use: {
        ...devices["Desktop Chrome"],
      },
    },

    // Full test suite - Desktop Chrome
    {
      name: "chromium",
      testIgnore: /.*\.smoke\.spec\.ts/,
      use: {
        ...devices["Desktop Chrome"],
      },
    },

    // Full test suite - Firefox
    {
      name: "firefox",
      testIgnore: /.*\.smoke\.spec\.ts/,
      use: {
        ...devices["Desktop Firefox"],
      },
    },

    // Mobile Safari
    {
      name: "mobile-safari",
      testMatch: /.*\.mobile\.spec\.ts/,
      use: {
        ...devices["iPhone 13"],
      },
    },
  ],

  // Folder for test artifacts
  outputDir: "playwright/test-results/artifacts",

  // Web server configuration
  webServer: {
    command: process.env.CI
      ? "PLAYWRIGHT_TEST_MODE=true NEXT_PUBLIC_TEST_MODE=true PORT=3000 pnpm start"
      : "PLAYWRIGHT_TEST_MODE=true NEXT_PUBLIC_TEST_MODE=true PORT=3000 pnpm dev",
    url: baseURL,
    reuseExistingServer: true,
    timeout: 120000,
  },

  // Global timeout
  timeout: 60000,

  // Expect timeout
  expect: {
    timeout: 10000,
  },
});
