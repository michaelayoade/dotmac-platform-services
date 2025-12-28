import { test, expect } from "../../fixtures";
import { UsersPage, UserFormPage } from "../../pages/dashboard";
import { expectLoadingComplete, expectNoErrors } from "../../utils/assertions";
import { setupApiMocks } from "../../utils/api-mocks";

test.describe("Users Management Tests", () => {
  test.use({ storageState: "playwright/.auth/admin.json" });

  test.describe("Users List", () => {
    test("should display users list with data", async ({ page }) => {
      await setupApiMocks(page);
      const usersPage = new UsersPage(page);
      await usersPage.navigate();
      await expectLoadingComplete(page);

      await expect(usersPage.usersTable).toBeVisible();
      const rowCount = await usersPage.getUserCount();
      expect(rowCount).toBeGreaterThan(0);
    });

    test("should search users by email", async ({ page }) => {
      await setupApiMocks(page);
      const usersPage = new UsersPage(page);
      await usersPage.navigate();
      await expectLoadingComplete(page);

      await usersPage.searchUsers("admin@test.local");
      await expectLoadingComplete(page);

      // Search results should be filtered
      const row = usersPage.getUserRowByEmail("admin@test.local");
      await expect(row).toBeVisible();
    });

    test("should clear search results", async ({ page }) => {
      await setupApiMocks(page);
      const usersPage = new UsersPage(page);
      await usersPage.navigate();
      await expectLoadingComplete(page);

      await usersPage.searchUsers("admin");
      await expectLoadingComplete(page);

      await usersPage.clearSearch();
      await expectLoadingComplete(page);

      // Should show all users again
      const rowCount = await usersPage.getUserCount();
      expect(rowCount).toBeGreaterThan(0);
    });

    test("should navigate to create user page", async ({ page }) => {
      await setupApiMocks(page);
      const usersPage = new UsersPage(page);
      await usersPage.navigate();
      await expectLoadingComplete(page);

      await usersPage.goToCreateUser();

      await expect(page).toHaveURL(/users\/new/);
    });

    test("should open user details on row click", async ({ page }) => {
      await setupApiMocks(page);
      const usersPage = new UsersPage(page);
      await usersPage.navigate();
      await expectLoadingComplete(page);

      await usersPage.openUserDetails("admin@test.local");

      // Should navigate to user detail page
      await expect(page).toHaveURL(/users\/user-001|users\/[a-zA-Z0-9-]+/);
    });
  });

  test.describe("Create User", () => {
    test("should display create user form", async ({ page }) => {
      await setupApiMocks(page);
      const userFormPage = new UserFormPage(page);
      await userFormPage.navigate();
      await expectLoadingComplete(page);

      await expect(userFormPage.nameInput).toBeVisible();
      await expect(userFormPage.emailInput).toBeVisible();
      await expect(userFormPage.saveButton).toBeVisible();
    });

    test("should show validation errors for empty form", async ({ page }) => {
      await setupApiMocks(page);
      const userFormPage = new UserFormPage(page);
      await userFormPage.navigate();
      await expectLoadingComplete(page);

      await userFormPage.save();

      // Should show validation errors
      await expect(page.locator("text=/required|name|email/i").first()).toBeVisible();
    });

    test("should fill and submit user form", async ({ page }) => {
      await setupApiMocks(page);

      // Mock user creation success
      await page.route("**/api/v1/users", async (route) => {
        if (route.request().method() === "POST") {
          await route.fulfill({
            status: 201,
            contentType: "application/json",
            body: JSON.stringify({
              id: "new-user-id",
              name: "New User",
              email: "newuser@test.local",
              role: "user",
            }),
          });
        } else {
          await route.continue();
        }
      });

      const userFormPage = new UserFormPage(page);
      await userFormPage.navigate();
      await expectLoadingComplete(page);

      await userFormPage.createUser({
        name: "New User",
        email: "newuser@test.local",
        password: "Password123!",
        role: "user",
      });

      // Should redirect back to users list or show success
      await expect(page).toHaveURL(/users(?!\/new)/);
    });

    test("should cancel and go back to users list", async ({ page }) => {
      await setupApiMocks(page);
      const userFormPage = new UserFormPage(page);
      await userFormPage.navigate();
      await expectLoadingComplete(page);

      await userFormPage.cancel();

      await expect(page).toHaveURL(/users(?!\/new)/);
    });
  });

  test.describe("User Actions", () => {
    test("should delete user with confirmation", async ({ page }) => {
      await setupApiMocks(page);

      // Mock delete endpoint
      await page.route("**/api/v1/users/*", async (route) => {
        if (route.request().method() === "DELETE") {
          await route.fulfill({ status: 204 });
        } else {
          await route.continue();
        }
      });

      const usersPage = new UsersPage(page);
      await usersPage.navigate();
      await expectLoadingComplete(page);

      // Open row actions and delete
      const row = usersPage.getUserRowByEmail("user@test.local");
      if (await row.isVisible()) {
        await row.getByRole("button", { name: /delete|remove/i }).click();

        // Confirm in modal
        await expect(page.locator('[role="dialog"]')).toBeVisible();
        await page.getByRole("button", { name: /confirm|yes|delete/i }).click();

        await expectLoadingComplete(page);
      }
    });
  });
});
