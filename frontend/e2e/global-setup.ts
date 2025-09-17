import { FullConfig } from '@playwright/test';
import { spawn, ChildProcess } from 'child_process';
import path from 'path';

/**
 * Global setup for E2E tests
 * Starts backend services and prepares test environment
 */
async function globalSetup(config: FullConfig) {
  console.log('🚀 Starting E2E test environment...');

  // Set test environment variables
  process.env.NODE_ENV = 'test';
  process.env.DOTMAC_JWT_SECRET_KEY = 'test-secret-key-for-e2e-tests';
  process.env.DOTMAC_REDIS_URL = 'redis://localhost:6379/1';
  process.env.DATABASE_URL = 'sqlite:///tmp/e2e_test.db';

  // Wait for services to be ready
  await waitForService('http://localhost:8000/health', 'Backend API');
  await waitForService('http://localhost:3000', 'Frontend App');

  // Create test data
  await createTestData();

  console.log('✅ E2E test environment ready');
}

/**
 * Wait for a service to become available
 */
async function waitForService(url: string, name: string, timeout = 60000) {
  const start = Date.now();

  while (Date.now() - start < timeout) {
    try {
      const response = await fetch(url);
      if (response.ok) {
        console.log(`✅ ${name} is ready at ${url}`);
        return;
      }
    } catch (error) {
      // Service not ready yet
    }

    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  throw new Error(`❌ ${name} did not start within ${timeout}ms`);
}

/**
 * Create test data via API calls
 */
async function createTestData() {
  const baseUrl = 'http://localhost:8000';

  try {
    // Create test admin user
    const adminResponse = await fetch(`${baseUrl}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'admin@test.com',
        password: 'Test123!@#',
        username: 'testadmin',
        full_name: 'Test Admin',
        roles: ['admin']
      })
    });

    if (adminResponse.ok) {
      console.log('✅ Test admin user created');
    }

    // Create test regular user
    const userResponse = await fetch(`${baseUrl}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'user@test.com',
        password: 'Test123!@#',
        username: 'testuser',
        full_name: 'Test User',
        roles: ['user']
      })
    });

    if (userResponse.ok) {
      console.log('✅ Test regular user created');
    }

    // Create test API key
    // First login as admin
    const loginResponse = await fetch(`${baseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'admin@test.com',
        password: 'Test123!@#'
      })
    });

    if (loginResponse.ok) {
      const { access_token } = await loginResponse.json();

      // Create API key
      const apiKeyResponse = await fetch(`${baseUrl}/auth/api-keys`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${access_token}`
        },
        body: JSON.stringify({
          name: 'E2E Test API Key',
          scopes: ['read:users', 'write:users'],
          expires_at: null
        })
      });

      if (apiKeyResponse.ok) {
        console.log('✅ Test API key created');
      }
    }

    console.log('✅ Test data created successfully');
  } catch (error) {
    console.log('⚠️  Test data creation failed (might already exist):', error.message);
  }
}

export default globalSetup;