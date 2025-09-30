import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DashboardPage from '../app/dashboard/page';
import { useRouter } from 'next/navigation';

// Mock Next.js router
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

// Mock auth lib
jest.mock('@/lib/auth', () => ({
  getCurrentUser: jest.fn(),
  logout: jest.fn(),
}));

// Mock config and logger
jest.mock('@/lib/config', () => ({
  platformConfig: {
    apiBaseUrl: 'http://localhost:8000',
  },
}));

jest.mock('@/lib/utils/logger', () => ({
  logger: {
    error: jest.fn(),
  },
}));

// Mock fetch globally
global.fetch = jest.fn();

import { getCurrentUser, logout } from '@/lib/auth';
import { logger } from '@/lib/utils/logger';

describe('DashboardPage', () => {
  const mockPush = jest.fn();
  const mockReplace = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
      replace: mockReplace,
    });
  });

  it('renders loading state initially', () => {
    // Mock to never resolve
    (getCurrentUser as jest.Mock).mockImplementation(() => new Promise(() => {}));
    (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));

    render(<DashboardPage />);

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders user information and health status when loaded', async () => {
    // Mock successful user fetch
    (getCurrentUser as jest.Mock).mockResolvedValueOnce({
      id: 'user-123',
      email: 'alice@example.com',
      roles: ['admin', 'user'],
    });

    // Mock successful health fetch
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: 'healthy',
        service: 'api-gateway',
        version: '1.0.0',
      }),
    });

    render(<DashboardPage />);

    // Wait for data to load
    await waitFor(() => {
      expect(screen.getByText('Welcome back, alice@example.com')).toBeInTheDocument();
    });

    // Check user info
    expect(screen.getByText('User Profile')).toBeInTheDocument();
    expect(screen.getByText('alice@example.com')).toBeInTheDocument();
    expect(screen.getByText('user-123')).toBeInTheDocument();
    expect(screen.getByText('admin, user')).toBeInTheDocument();

    // Check API health
    expect(screen.getByText('API Status')).toBeInTheDocument();
    expect(screen.getByText('healthy')).toBeInTheDocument();
    expect(screen.getByText('api-gateway')).toBeInTheDocument();
    expect(screen.getByText('1.0.0')).toBeInTheDocument();
  });

  it('redirects to login when user fetch fails', async () => {
    // Mock failed user fetch
    (getCurrentUser as jest.Mock).mockRejectedValueOnce(new Error('Unauthorized'));

    // Mock health fetch
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    render(<DashboardPage />);

    // Wait for redirect
    await waitFor(() => {
      expect(logger.error).toHaveBeenCalledWith(
        'Failed to fetch user',
        expect.any(Error)
      );
      expect(mockReplace).toHaveBeenCalledWith('/login');
    });
  });

  it('handles health check failure gracefully', async () => {
    // Mock successful user fetch
    (getCurrentUser as jest.Mock).mockResolvedValueOnce({
      id: 'user-123',
      email: 'alice@example.com',
    });

    // Mock failed health fetch
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

    render(<DashboardPage />);

    // Wait for error handling
    await waitFor(() => {
      expect(logger.error).toHaveBeenCalledWith(
        'Failed to fetch health status',
        expect.any(Error)
      );
    });

    // Should still render user info
    expect(screen.getByText('Welcome back, alice@example.com')).toBeInTheDocument();
    expect(screen.getByText('Unable to fetch status')).toBeInTheDocument();
  });

  it('handles logout correctly', async () => {
    const user = userEvent.setup();

    // Mock successful user fetch
    (getCurrentUser as jest.Mock).mockResolvedValueOnce({
      id: 'user-123',
      email: 'alice@example.com',
    });

    // Mock health fetch
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    // Mock logout
    (logout as jest.Mock).mockResolvedValueOnce(undefined);

    render(<DashboardPage />);

    // Wait for render
    await waitFor(() => {
      expect(screen.getByText('Sign out')).toBeInTheDocument();
    });

    // Click logout
    await user.click(screen.getByText('Sign out'));

    await waitFor(() => {
      expect(logout).toHaveBeenCalled();
      expect(mockPush).toHaveBeenCalledWith('/login');
    });
  });

  it('renders platform services grid', async () => {
    // Mock successful user fetch
    (getCurrentUser as jest.Mock).mockResolvedValueOnce({
      id: 'user-123',
      email: 'alice@example.com',
    });

    // Mock health fetch
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    render(<DashboardPage />);

    // Wait for render
    await waitFor(() => {
      expect(screen.getByText('Platform Services')).toBeInTheDocument();
    });

    // Check services are rendered
    expect(screen.getByText('Authentication')).toBeInTheDocument();
    expect(screen.getByText('File Storage')).toBeInTheDocument();
    expect(screen.getByText('Secrets Manager')).toBeInTheDocument();
    expect(screen.getByText('Analytics')).toBeInTheDocument();
    expect(screen.getByText('Communications')).toBeInTheDocument();
    expect(screen.getByText('Search')).toBeInTheDocument();
    expect(screen.getByText('Data Transfer')).toBeInTheDocument();
    expect(screen.getByText('API Gateway')).toBeInTheDocument();
  });

  it('renders quick actions links', async () => {
    // Mock successful user fetch
    (getCurrentUser as jest.Mock).mockResolvedValueOnce({
      id: 'user-123',
      email: 'alice@example.com',
    });

    // Mock health fetch
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    render(<DashboardPage />);

    // Wait for render
    await waitFor(() => {
      expect(screen.getByText('Quick Actions')).toBeInTheDocument();
    });

    // Check quick action links
    const customersLink = screen.getByText('Manage Customers');
    const billingLink = screen.getByText('Billing Overview');
    const apiKeysLink = screen.getByText('Manage API Keys');

    expect(customersLink).toHaveAttribute('href', '/dashboard/customers');
    expect(billingLink).toHaveAttribute('href', '/dashboard/billing');
    expect(apiKeysLink).toHaveAttribute('href', '/dashboard/api-keys');
  });
});
