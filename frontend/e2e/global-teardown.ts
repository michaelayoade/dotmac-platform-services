import { FullConfig } from "@playwright/test";
import fs from "fs";
import path from "path";

/**
 * Global teardown for Playwright tests
 * Cleanup after all tests have completed
 */
async function globalTeardown(config: FullConfig) {
  console.log("Running global teardown...");

  // Clean up auth state files
  const authDir = path.join(__dirname, "../playwright/.auth");
  if (fs.existsSync(authDir)) {
    try {
      const files = fs.readdirSync(authDir);
      for (const file of files) {
        if (file.endsWith(".json")) {
          fs.unlinkSync(path.join(authDir, file));
          console.log(`  Cleaned up auth state: ${file}`);
        }
      }
    } catch (error) {
      console.warn("  Warning: Could not clean up auth files:", error);
    }
  }

  // Clean up any test artifacts older than 7 days
  const artifactsDir = path.join(__dirname, "../playwright/test-results");
  if (fs.existsSync(artifactsDir)) {
    try {
      cleanOldArtifacts(artifactsDir, 7);
    } catch (error) {
      console.warn("  Warning: Could not clean up old artifacts:", error);
    }
  }

  // Clean up screenshots directory
  const screenshotsDir = path.join(artifactsDir, "screenshots");
  if (fs.existsSync(screenshotsDir)) {
    try {
      const files = fs.readdirSync(screenshotsDir);
      console.log(`  Found ${files.length} screenshots to review`);
    } catch (error) {
      // Ignore
    }
  }

  // If running with a real backend, clean up test data via API
  const apiUrl = process.env.PLAYWRIGHT_API_URL || "http://localhost:8000";
  const cleanupEnabled = process.env.PLAYWRIGHT_CLEANUP_TEST_DATA === "true";

  if (cleanupEnabled) {
    await cleanupTestData(apiUrl);
  }

  console.log("Global teardown completed");
}

/**
 * Clean up old artifacts to prevent disk bloat
 */
function cleanOldArtifacts(dir: string, daysOld: number): void {
  const now = Date.now();
  const maxAge = daysOld * 24 * 60 * 60 * 1000;

  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      // Recursively clean subdirectories
      cleanOldArtifacts(fullPath, daysOld);

      // Remove empty directories
      const subEntries = fs.readdirSync(fullPath);
      if (subEntries.length === 0) {
        fs.rmdirSync(fullPath);
      }
    } else {
      const stats = fs.statSync(fullPath);
      if (now - stats.mtimeMs > maxAge) {
        fs.unlinkSync(fullPath);
      }
    }
  }
}

/**
 * Clean up test data created during test runs
 * Only runs when PLAYWRIGHT_CLEANUP_TEST_DATA=true
 */
async function cleanupTestData(apiUrl: string): Promise<void> {
  console.log("  Cleaning up test data via API...");

  // Test data prefixes to clean up
  const testPrefixes = {
    users: "test-user-",
    tenants: "test-tenant-",
    invoices: "test-inv-",
  };

  for (const [resource, prefix] of Object.entries(testPrefixes)) {
    try {
      // This is a placeholder - implement actual cleanup API calls
      // Example: DELETE /api/v1/test/cleanup?prefix=test-user-
      const response = await fetch(
        `${apiUrl}/api/v1/test/cleanup?resource=${resource}&prefix=${prefix}`,
        {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
            // Use a test cleanup token if configured
            Authorization: `Bearer ${process.env.PLAYWRIGHT_CLEANUP_TOKEN || ""}`,
          },
        }
      );

      if (response.ok) {
        const result = await response.json();
        console.log(`    Cleaned ${result.deleted || 0} ${resource}`);
      }
    } catch (error) {
      // Cleanup endpoint may not exist - that's OK
      console.log(`    Skipped ${resource} cleanup (endpoint not available)`);
    }
  }
}

export default globalTeardown;
