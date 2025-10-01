/**
 * Auth utility tests aligned with cookie-based authentication flow.
 */

global.fetch = jest.fn();

describe('auth utilities', () => {
  beforeEach(() => {
    fetch.mockReset();
    // Mock environment for testing
    process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8000';
  });

  afterEach(() => {
    jest.restoreAllMocks();
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
  });

  test('login sends credentials with cookie support', async () => {
    const mockJson = { success: true };
    const mockHeaders = new Map();
    mockHeaders.entries = jest.fn(() => [].entries());

    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue(mockJson),
      headers: mockHeaders,
      status: 200,
    };
    fetch.mockResolvedValue(mockResponse);

    const { login } = require('../lib/auth');

    const result = await login({ email: 'user@example.com', password: 'secret' });

    // In test environment (jsdom), platformConfig.apiBaseUrl is '' (empty string for client-side)
    // So we expect relative URLs
    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/auth/login/cookie',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'user@example.com', password: 'secret' }),
      })
    );
    expect(mockResponse.json).toHaveBeenCalledTimes(1);
    expect(result).toEqual(mockJson);
  });

  test('login throws with API error detail', async () => {
    const mockHeaders = new Map();
    mockHeaders.entries = jest.fn(() => [].entries());

    const mockResponse = {
      ok: false,
      json: jest.fn().mockResolvedValue({ detail: 'Invalid username or password' }),
      status: 401,
      headers: mockHeaders,
    };
    fetch.mockResolvedValue(mockResponse);

    const { login } = require('../lib/auth');

    await expect(login({ email: 'bad@example.com', password: 'nope' }))
      .rejects.toThrow('Invalid username or password');
  });

  test('register posts form data and relies on cookies', async () => {
    const mockJson = {
      access_token: 'token',
      refresh_token: 'refresh',
      token_type: 'bearer',
    };
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue(mockJson),
    };
    fetch.mockResolvedValue(mockResponse);

    const { register } = require('../lib/auth');

    const result = await register({ email: 'user@example.com', password: 'secret', name: 'User' });

    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/auth/register',
      expect.objectContaining({
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: 'user',
          email: 'user@example.com',
          password: 'secret',
          full_name: 'User',
        }),
      })
    );
    expect(result).toEqual(mockJson);
  });

  test('getCurrentUser fetches with credentials include', async () => {
    const mockUser = { id: '1', email: 'user@example.com' };
    const mockResponse = {
      ok: true,
      json: jest.fn().mockResolvedValue(mockUser),
    };
    fetch.mockResolvedValue(mockResponse);

    const { getCurrentUser } = require('../lib/auth');

    const result = await getCurrentUser();

    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/auth/me',
      { credentials: 'include' }
    );
    expect(result).toEqual(mockUser);
  });

  test('getCurrentUser throws on failure', async () => {
    const mockResponse = { ok: false, status: 401 };
    fetch.mockResolvedValue(mockResponse);

    const { getCurrentUser } = require('../lib/auth');

    await expect(getCurrentUser()).rejects.toThrow('Failed to fetch user');
  });

  test('logout posts to logout endpoint', async () => {
    const mockResponse = { ok: true };
    fetch.mockResolvedValue(mockResponse);

    const { logout } = require('../lib/auth');

    await logout();

    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/auth/logout',
      { method: 'POST', credentials: 'include' }
    );
  });

  test('isAuthenticated returns true when verify succeeds', async () => {
    const mockResponse = { ok: true };
    fetch.mockResolvedValue(mockResponse);

    const { isAuthenticated } = require('../lib/auth');

    await expect(isAuthenticated()).resolves.toBe(true);
    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/auth/verify',
      { credentials: 'include' }
    );
  });

  test('isAuthenticated returns false when verify fails', async () => {
    const mockResponse = { ok: false };
    fetch.mockResolvedValue(mockResponse);

    const { isAuthenticated } = require('../lib/auth');

    await expect(isAuthenticated()).resolves.toBe(false);
  });

  test('saveTokens logs informational message', () => {
    const logSpy = jest.spyOn(console, 'log').mockImplementation(() => {});

    const { saveTokens } = require('../lib/auth');

    saveTokens({ access_token: 'token', refresh_token: 'refresh', token_type: 'bearer' });

    expect(logSpy).toHaveBeenCalled();
  });

  test('getAccessToken always returns null for HttpOnly cookies', () => {
    const { getAccessToken } = require('../lib/auth');

    expect(getAccessToken()).toBeNull();
  });

  test('clearTokens logs intention but performs no client action', () => {
    const logSpy = jest.spyOn(console, 'log').mockImplementation(() => {});

    const { clearTokens } = require('../lib/auth');

    clearTokens();

    expect(logSpy).toHaveBeenCalled();
  });
});
