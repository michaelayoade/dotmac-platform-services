import { test, expect } from '@playwright/test';
import { GraphQLTestHelper } from '../utils/graphql-helper';

test.describe('GraphQL API Integration', () => {
  let graphqlHelper: GraphQLTestHelper;

  test.beforeEach(async ({ page }) => {
    graphqlHelper = new GraphQLTestHelper(page);
    await graphqlHelper.authenticate('admin@test.com', 'Test123!@#');
  });

  test.describe('GraphQL Queries', () => {
    test('should execute user query and display results', async ({ page }) => {
      // Execute GraphQL query
      const query = `
        query GetUsers($limit: Int) {
          users(limit: $limit) {
            id
            email
            fullName
            roles
            createdAt
          }
        }
      `;

      const response = await graphqlHelper.executeQuery(query, { limit: 10 });
      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(data.data.users).toBeDefined();
      expect(Array.isArray(data.data.users)).toBe(true);

      // Navigate to GraphQL playground in UI
      await page.goto('/graphql-playground');

      // Verify schema is loaded
      await expect(page.locator('.schema-explorer')).toBeVisible();
      await expect(page.locator('text="User"')).toBeVisible();
    });

    test('should handle GraphQL errors in UI', async ({ page }) => {
      await page.goto('/admin/analytics');

      // Intercept GraphQL request to return error
      await page.route('**/graphql', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            errors: [
              {
                message: 'Field "invalidField" doesn\'t exist on type "User"',
                locations: [{ line: 3, column: 5 }],
                path: ['users']
              }
            ]
          })
        });
      });

      // Trigger GraphQL query from UI
      await page.click('[data-testid="load-analytics"]');

      // Verify error handling
      await expect(page.locator('.graphql-error')).toBeVisible();
      await expect(page.locator('.graphql-error')).toContainText('GraphQL Error');
    });

    test('should execute complex nested query', async ({ page }) => {
      const query = `
        query GetUserWithPermissions($userId: ID!) {
          user(id: $userId) {
            id
            email
            fullName
            roles
            permissions {
              id
              name
              resource
              actions
            }
            tenant {
              id
              name
              settings {
                maxUsers
                features
              }
            }
          }
        }
      `;

      // Create test user first
      const user = await graphqlHelper.createTestUser();

      const response = await graphqlHelper.executeQuery(query, { userId: user.id });
      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(data.data.user).toBeDefined();
      expect(data.data.user.permissions).toBeDefined();
      expect(data.data.user.tenant).toBeDefined();

      // Navigate to user details page
      await page.goto(`/admin/users/${user.id}`);

      // Verify nested data is displayed
      await expect(page.locator('[data-testid="user-permissions"]')).toBeVisible();
      await expect(page.locator('[data-testid="user-tenant"]')).toBeVisible();
    });
  });

  test.describe('GraphQL Mutations', () => {
    test('should create user via GraphQL mutation', async ({ page }) => {
      const mutation = `
        mutation CreateUser($input: CreateUserInput!) {
          createUser(input: $input) {
            id
            email
            fullName
            roles
          }
        }
      `;

      const input = {
        email: 'graphql-user@test.com',
        fullName: 'GraphQL Test User',
        password: 'Test123!@#',
        roles: ['user']
      };

      const response = await graphqlHelper.executeMutation(mutation, { input });
      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(data.data.createUser).toBeDefined();
      expect(data.data.createUser.email).toBe(input.email);

      // Navigate to users page and verify user appears
      await page.goto('/admin/users');
      await expect(page.locator(`text=${input.fullName}`)).toBeVisible();
    });

    test('should update user via GraphQL mutation and reflect in UI', async ({ page }) => {
      // Create user first
      const user = await graphqlHelper.createTestUser();

      // Navigate to user edit page
      await page.goto(`/admin/users/${user.id}/edit`);

      const mutation = `
        mutation UpdateUser($id: ID!, $input: UpdateUserInput!) {
          updateUser(id: $id, input: $input) {
            id
            fullName
            email
          }
        }
      `;

      const input = { fullName: 'Updated via GraphQL' };

      const response = await graphqlHelper.executeMutation(mutation, { id: user.id, input });
      expect(response.status()).toBe(200);

      // Refresh page and verify update
      await page.reload();
      await expect(page.locator('input[name="fullName"]')).toHaveValue('Updated via GraphQL');
    });

    test('should handle mutation validation errors', async ({ page }) => {
      await page.goto('/admin/users/create');

      // Intercept GraphQL mutation to return validation error
      await page.route('**/graphql', route => {
        const requestBody = JSON.parse(route.request().postData() || '{}');
        if (requestBody.query?.includes('createUser')) {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              errors: [
                {
                  message: 'Validation failed',
                  extensions: {
                    code: 'VALIDATION_ERROR',
                    fields: {
                      email: 'Email already exists'
                    }
                  }
                }
              ]
            })
          });
        } else {
          route.continue();
        }
      });

      // Fill form and submit (assuming form uses GraphQL)
      await page.fill('input[name="email"]', 'existing@test.com');
      await page.fill('input[name="fullName"]', 'Test User');
      await page.fill('input[name="password"]', 'Test123!@#');
      await page.click('button[type="submit"]');

      // Verify error display
      await expect(page.locator('.field-error')).toContainText('Email already exists');
    });
  });

  test.describe('GraphQL Subscriptions', () => {
    test('should receive real-time updates via GraphQL subscription', async ({ page }) => {
      await page.goto('/admin/users');

      // Start GraphQL subscription for user updates
      const subscription = `
        subscription UserUpdates {
          userUpdated {
            id
            email
            fullName
            lastUpdated
          }
        }
      `;

      // Set up subscription listener in the UI
      await page.evaluate((sub) => {
        // This would be handled by your GraphQL client (e.g., Apollo Client)
        window.startSubscription(sub);
      }, subscription);

      // Create a user via mutation to trigger subscription
      const user = await graphqlHelper.createTestUser();

      // Update the user to trigger subscription event
      await graphqlHelper.executeMutation(`
        mutation UpdateUser($id: ID!, $input: UpdateUserInput!) {
          updateUser(id: $id, input: $input) {
            id
            fullName
          }
        }
      `, {
        id: user.id,
        input: { fullName: 'Real-time Updated User' }
      });

      // Verify real-time update appears in UI
      await expect(page.locator(`[data-user-id="${user.id}"]`)).toContainText('Real-time Updated User');
      await expect(page.locator('.realtime-indicator')).toBeVisible();
    });

    test('should handle subscription connection issues', async ({ page }) => {
      await page.goto('/admin/dashboard');

      // Simulate WebSocket connection failure
      await page.evaluate(() => {
        // Mock WebSocket to fail
        window.WebSocket = class extends EventTarget {
          constructor() {
            super();
            setTimeout(() => {
              this.dispatchEvent(new Event('error'));
            }, 100);
          }
          close() {}
          send() {}
        };
      });

      // Try to establish subscription
      await page.click('[data-testid="enable-realtime"]');

      // Verify error handling
      await expect(page.locator('.subscription-error')).toBeVisible();
      await expect(page.locator('.reconnect-button')).toBeVisible();
    });
  });

  test.describe('GraphQL Schema Introspection', () => {
    test('should load schema in GraphQL playground', async ({ page }) => {
      await page.goto('/graphql-playground');

      // Verify schema introspection works
      await expect(page.locator('.schema-explorer')).toBeVisible();

      // Check for key types
      await expect(page.locator('text="User"')).toBeVisible();
      await expect(page.locator('text="Query"')).toBeVisible();
      await expect(page.locator('text="Mutation"')).toBeVisible();
      await expect(page.locator('text="Subscription"')).toBeVisible();

      // Click on User type to expand
      await page.click('text="User"');

      // Verify User fields are shown
      await expect(page.locator('text="id: ID!"')).toBeVisible();
      await expect(page.locator('text="email: String!"')).toBeVisible();
      await expect(page.locator('text="fullName: String"')).toBeVisible();
    });

    test('should execute query from playground', async ({ page }) => {
      await page.goto('/graphql-playground');

      // Enter a query in the playground
      const query = `
        query {
          users(limit: 5) {
            id
            email
            fullName
          }
        }
      `;

      await page.fill('.query-editor', query);
      await page.click('.execute-button');

      // Verify results appear
      await expect(page.locator('.result-viewer')).toBeVisible();
      await expect(page.locator('.result-viewer')).toContainText('"data"');
      await expect(page.locator('.result-viewer')).toContainText('"users"');
    });

    test('should show query validation errors in playground', async ({ page }) => {
      await page.goto('/graphql-playground');

      // Enter invalid query
      const invalidQuery = `
        query {
          users {
            invalidField
          }
        }
      `;

      await page.fill('.query-editor', invalidQuery);
      await page.click('.execute-button');

      // Verify validation error is shown
      await expect(page.locator('.error-viewer')).toBeVisible();
      await expect(page.locator('.error-viewer')).toContainText('Cannot query field "invalidField"');
    });
  });

  test.describe('GraphQL Performance', () => {
    test('should handle large query results efficiently', async ({ page }) => {
      const largeQuery = `
        query GetManyUsers {
          users(limit: 1000) {
            id
            email
            fullName
            createdAt
            roles
            permissions {
              id
              name
              resource
            }
          }
        }
      `;

      const startTime = Date.now();
      const response = await graphqlHelper.executeQuery(largeQuery);
      const endTime = Date.now();

      expect(response.status()).toBe(200);

      const data = await response.json();
      expect(data.data.users).toBeDefined();

      // Verify reasonable performance (adjust threshold as needed)
      expect(endTime - startTime).toBeLessThan(5000); // Should complete within 5 seconds
    });

    test('should implement query batching', async ({ page }) => {
      // Execute multiple queries in batch
      const queries = [
        { query: '{ users(limit: 5) { id email } }', operationName: 'GetUsers' },
        { query: '{ currentUser { id email roles } }', operationName: 'GetCurrentUser' },
        { query: '{ permissions { id name } }', operationName: 'GetPermissions' }
      ];

      const batchResponse = await graphqlHelper.executeBatch(queries);
      expect(batchResponse.status()).toBe(200);

      const results = await batchResponse.json();
      expect(Array.isArray(results)).toBe(true);
      expect(results).toHaveLength(3);

      // Verify each query result
      results.forEach((result, index) => {
        expect(result.data).toBeDefined();
      });
    });

    test('should handle query depth limiting', async ({ page }) => {
      // Attempt deeply nested query that should be limited
      const deepQuery = `
        query DeepQuery {
          users {
            tenant {
              users {
                tenant {
                  users {
                    tenant {
                      users {
                        id
                      }
                    }
                  }
                }
              }
            }
          }
        }
      `;

      const response = await graphqlHelper.executeQuery(deepQuery);

      // Should return error due to depth limiting
      const data = await response.json();
      expect(data.errors).toBeDefined();
      expect(data.errors[0].message).toContain('Query depth limit exceeded');
    });
  });
});