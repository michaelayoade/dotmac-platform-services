/**
 * Basic tests for auth utilities
 * Note: This is a simplified test setup since the frontend was cleaned up
 */

// Mock localStorage for Node.js environment
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock fetch for testing
global.fetch = jest.fn();

// Import auth utilities
const {
  saveTokens,
  getAccessToken,
  clearTokens,
  isAuthenticated
} = require('../lib/auth');

describe('Auth Utilities', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    localStorage.getItem.mockClear();
    localStorage.setItem.mockClear();
    localStorage.removeItem.mockClear();
    fetch.mockClear();
  });

  describe('saveTokens', () => {
    test('should save access token to localStorage', () => {
      const tokens = {
        access_token: 'test-access-token',
        refresh_token: 'test-refresh-token',
        token_type: 'bearer'
      };

      saveTokens(tokens);

      expect(localStorage.setItem).toHaveBeenCalledWith('access_token', 'test-access-token');
      expect(localStorage.setItem).toHaveBeenCalledWith('refresh_token', 'test-refresh-token');
    });

    test('should save access token without refresh token', () => {
      const tokens = {
        access_token: 'test-access-token',
        token_type: 'bearer'
      };

      saveTokens(tokens);

      expect(localStorage.setItem).toHaveBeenCalledWith('access_token', 'test-access-token');
      expect(localStorage.setItem).not.toHaveBeenCalledWith('refresh_token', expect.anything());
    });
  });

  describe('getAccessToken', () => {
    test('should return access token from localStorage', () => {
      localStorage.getItem.mockReturnValue('stored-access-token');

      const token = getAccessToken();

      expect(localStorage.getItem).toHaveBeenCalledWith('access_token');
      expect(token).toBe('stored-access-token');
    });

    test('should return null if no token stored', () => {
      localStorage.getItem.mockReturnValue(null);

      const token = getAccessToken();

      expect(token).toBeNull();
    });
  });

  describe('clearTokens', () => {
    test('should remove both tokens from localStorage', () => {
      clearTokens();

      expect(localStorage.removeItem).toHaveBeenCalledWith('access_token');
      expect(localStorage.removeItem).toHaveBeenCalledWith('refresh_token');
    });
  });

  describe('isAuthenticated', () => {
    test('should return true when access token exists', () => {
      localStorage.getItem.mockReturnValue('some-token');

      const authenticated = isAuthenticated();

      expect(authenticated).toBe(true);
    });

    test('should return false when no access token', () => {
      localStorage.getItem.mockReturnValue(null);

      const authenticated = isAuthenticated();

      expect(authenticated).toBe(false);
    });
  });

  describe('login function', () => {
    test('should make correct API request', async () => {
      // Mock successful response
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          access_token: 'new-token',
          refresh_token: 'new-refresh-token',
          token_type: 'bearer'
        })
      };
      fetch.mockResolvedValue(mockResponse);

      const { login } = require('../lib/auth');

      const credentials = {
        email: 'test@example.com',
        password: 'password123'
      };

      const result = await login(credentials);

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/auth/login',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: 'test@example.com',
            password: 'password123',
          }),
        }
      );

      expect(result).toEqual({
        access_token: 'new-token',
        refresh_token: 'new-refresh-token',
        token_type: 'bearer'
      });
    });

    test('should handle login error', async () => {
      // Mock error response
      const mockResponse = {
        ok: false,
        json: jest.fn().mockResolvedValue({
          detail: 'Invalid credentials'
        })
      };
      fetch.mockResolvedValue(mockResponse);

      const { login } = require('../lib/auth');

      const credentials = {
        email: 'wrong@example.com',
        password: 'wrongpassword'
      };

      await expect(login(credentials)).rejects.toThrow('Invalid credentials');
    });

    test('should handle network error', async () => {
      // Mock network failure
      fetch.mockRejectedValue(new Error('Network error'));

      const { login } = require('../lib/auth');

      const credentials = {
        email: 'test@example.com',
        password: 'password123'
      };

      await expect(login(credentials)).rejects.toThrow('Network error');
    });
  });

  describe('getCurrentUser function', () => {
    test('should make correct API request with token', async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          id: 'user-123',
          email: 'test@example.com',
          username: 'testuser',
          roles: ['user']
        })
      };
      fetch.mockResolvedValue(mockResponse);

      const { getCurrentUser } = require('../lib/auth');

      const result = await getCurrentUser('test-token');

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/auth/me',
        {
          headers: {
            'Authorization': 'Bearer test-token',
          },
        }
      );

      expect(result).toEqual({
        id: 'user-123',
        email: 'test@example.com',
        username: 'testuser',
        roles: ['user']
      });
    });

    test('should handle unauthorized error', async () => {
      const mockResponse = {
        ok: false,
        status: 401
      };
      fetch.mockResolvedValue(mockResponse);

      const { getCurrentUser } = require('../lib/auth');

      await expect(getCurrentUser('invalid-token')).rejects.toThrow('Failed to fetch user');
    });
  });
});

// Additional integration-style tests
describe('Auth Integration Flow', () => {
  beforeEach(() => {
    localStorage.getItem.mockClear();
    localStorage.setItem.mockClear();
    localStorage.removeItem.mockClear();
    fetch.mockClear();
  });

  test('should complete full auth flow', async () => {
    // Mock successful login
    const loginResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        access_token: 'auth-token',
        refresh_token: 'refresh-token',
        token_type: 'bearer'
      })
    };

    // Mock successful user fetch
    const userResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue({
        id: 'user-123',
        email: 'test@example.com',
        username: 'testuser'
      })
    };

    fetch
      .mockResolvedValueOnce(loginResponse)  // First call for login
      .mockResolvedValueOnce(userResponse);  // Second call for getCurrentUser

    const { login, getCurrentUser, saveTokens } = require('../lib/auth');

    // 1. Login
    const tokens = await login({
      email: 'test@example.com',
      password: 'password123'
    });

    // 2. Save tokens
    saveTokens(tokens);
    expect(localStorage.setItem).toHaveBeenCalledWith('access_token', 'auth-token');

    // 3. Get current user
    const user = await getCurrentUser('auth-token');
    expect(user.email).toBe('test@example.com');
  });
});