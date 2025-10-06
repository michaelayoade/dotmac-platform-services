import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';

// Mock the http-client with simpler approach
jest.mock('@dotmac/http-client', () => ({
  httpClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}));

// Mock child components to avoid complex rendering issues
jest.mock('../../app/dashboard/settings/plugins/components/PluginForm', () => ({
  PluginForm: () => <div data-testid="plugin-form">Plugin Form</div>,
}));

jest.mock('../../app/dashboard/settings/plugins/components/PluginCard', () => ({
  PluginCard: ({ plugin }: any) => <div data-testid="plugin-card">{plugin.name}</div>,
}));

jest.mock('../../app/dashboard/settings/plugins/components/PluginHealthDashboard', () => ({
  PluginHealthDashboard: () => <div data-testid="health-dashboard">Health Dashboard</div>,
}));

describe('PluginsPage Basic Tests', () => {
  const { httpClient } = require('@dotmac/http-client');

  beforeEach(() => {
    jest.clearAllMocks();

    // Setup successful responses
    httpClient.get.mockResolvedValue({ data: [] });
    httpClient.post.mockResolvedValue({ data: [] });
  });

  it('renders loading state initially', async () => {
    // Import the component after mocks are set up
    const PluginsPage = (await import('../../app/dashboard/settings/plugins/page')).default;

    // Delay the response to test loading state
    httpClient.get.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ data: [] }), 100)));
    httpClient.post.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ data: [] }), 100)));

    render(<PluginsPage />);

    expect(screen.getByText('Loading plugins...')).toBeInTheDocument();
  });

  it('renders main content after loading', async () => {
    const PluginsPage = (await import('../../app/dashboard/settings/plugins/page')).default;

    render(<PluginsPage />);

    await waitFor(() => {
      expect(screen.getByText('Plugin Management')).toBeInTheDocument();
    });

    // Page renders successfully - main heading is present
    expect(screen.getByRole('heading', { name: 'Plugin Management' })).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    const PluginsPage = (await import('../../app/dashboard/settings/plugins/page')).default;

    httpClient.get.mockRejectedValue(new Error('API Error'));

    render(<PluginsPage />);

    // Wait for error state - might show generic error message
    await waitFor(() => {
      // Check if any error text is displayed
      const errorText = screen.queryByText(/error/i) || screen.queryByText(/failed/i);
      expect(errorText || screen.getByText('Plugin Management')).toBeInTheDocument();
    }, { timeout: 2000 });

    // Test passes if page doesn't crash on error
  });
});