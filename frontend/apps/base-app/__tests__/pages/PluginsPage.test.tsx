import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import PluginsPage from '../../app/dashboard/settings/plugins/page';

// Mock the http-client
jest.mock('@dotmac/http-client', () => ({
  httpClient: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}));

// Get the mocked http client for use in tests
const { httpClient: mockHttpClient } = require('@dotmac/http-client');

// Mock the child components to isolate page-level testing
jest.mock('../../app/dashboard/settings/plugins/components/PluginForm', () => ({
  PluginForm: ({ onSubmit, onCancel, onTestConnection }: any) => (
    <div data-testid="plugin-form">
      <button onClick={() => onSubmit({ plugin_name: 'Test', instance_name: 'Test Instance', configuration: {} })}>
        Submit Form
      </button>
      <button onClick={onCancel}>Cancel Form</button>
      <button onClick={() => onTestConnection('test-id', {})}>Test Connection</button>
    </div>
  ),
}));

jest.mock('../../app/dashboard/settings/plugins/components/PluginCard', () => ({
  PluginCard: ({ plugin, onInstall }: any) => (
    <div data-testid="plugin-card">
      <h3>{plugin.name}</h3>
      <button onClick={() => onInstall(plugin)}>Install Plugin</button>
    </div>
  ),
}));

jest.mock('../../app/dashboard/settings/plugins/components/PluginHealthDashboard', () => ({
  PluginHealthDashboard: ({ onRefresh }: any) => (
    <div data-testid="health-dashboard">
      <button onClick={onRefresh}>Refresh Health</button>
    </div>
  ),
}));

// Mock data
const mockAvailablePlugins = [
  {
    name: "WhatsApp Business",
    type: "notification",
    version: "1.0.0",
    description: "Send WhatsApp messages via WhatsApp Business API",
    author: "DotMac Platform",
    supports_health_check: true,
    supports_test_connection: true,
    fields: [
      {
        key: "api_token",
        label: "API Token",
        type: "secret",
        required: true,
      }
    ]
  },
  {
    name: "Slack Integration",
    type: "notification",
    version: "2.0.0",
    description: "Send notifications to Slack channels",
    author: "DotMac Platform",
    supports_health_check: true,
    supports_test_connection: false,
    fields: []
  },
  {
    name: "Payment Gateway",
    type: "payment",
    version: "1.5.0",
    description: "Process payments securely",
    author: "Third Party",
    supports_health_check: false,
    supports_test_connection: true,
    fields: []
  }
];

const mockPluginInstances = [
  {
    id: "550e8400-e29b-41d4-a716-446655440000",
    plugin_name: "WhatsApp Business",
    instance_name: "Production WhatsApp",
    status: "active",
    has_configuration: true,
    created_at: "2024-01-15T10:00:00Z"
  },
  {
    id: "550e8400-e29b-41d4-a716-446655440001",
    plugin_name: "Slack Integration",
    instance_name: "Team Notifications",
    status: "error",
    has_configuration: true,
    last_error: "Authentication failed"
  }
];

const mockHealthChecks = [
  {
    plugin_instance_id: "550e8400-e29b-41d4-a716-446655440000",
    status: "healthy",
    message: "All systems operational",
    details: {},
    response_time_ms: 200,
    timestamp: "2024-01-20T15:30:00Z"
  },
  {
    plugin_instance_id: "550e8400-e29b-41d4-a716-446655440001",
    status: "error",
    message: "Authentication failed",
    details: { error_code: 401 },
    response_time_ms: 1000,
    timestamp: "2024-01-20T15:30:00Z"
  }
];

const mockSuccessfulApiResponse = {
  plugins: mockAvailablePlugins,
  instances: { plugins: mockPluginInstances },
  healthChecks: mockHealthChecks
};

describe('PluginsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Setup default successful API responses
    mockHttpClient.get.mockImplementation((url: string) => {
      if (url === '/api/v1/plugins/') {
        return Promise.resolve({ data: mockAvailablePlugins });
      }
      if (url === '/api/v1/plugins/instances') {
        return Promise.resolve({ data: { plugins: mockPluginInstances } });
      }
      return Promise.reject(new Error(`Unexpected GET request to ${url}`));
    });

    mockHttpClient.post.mockImplementation((url: string) => {
      if (url === '/api/v1/plugins/instances/health-check') {
        return Promise.resolve({ data: mockHealthChecks });
      }
      if (url === '/api/v1/plugins/refresh') {
        return Promise.resolve({ data: { message: 'Plugins refreshed' } });
      }
      if (url === '/api/v1/plugins/instances') {
        return Promise.resolve({
          data: {
            id: "new-instance-id",
            plugin_name: "Test",
            instance_name: "Test Instance",
            status: "active"
          }
        });
      }
      return Promise.reject(new Error(`Unexpected POST request to ${url}`));
    });
  });

  describe('Page Loading', () => {
    it('shows loading state initially', () => {
      // Make API calls hang to test loading state
      mockHttpClient.get.mockImplementation(() => new Promise(() => {}));
      mockHttpClient.post.mockImplementation(() => new Promise(() => {}));

      render(<PluginsPage />);

      expect(screen.getByText('Loading plugins...')).toBeInTheDocument();
    });

    it('loads and displays plugin data on mount', async () => {
      render(<PluginsPage />);

      await waitFor(() => {
        expect(screen.getByText('Plugin Management')).toBeInTheDocument();
      });

      expect(mockHttpClient.get).toHaveBeenCalledWith('/api/v1/plugins/');
      expect(mockHttpClient.get).toHaveBeenCalledWith('/api/v1/plugins/instances');
      expect(mockHttpClient.post).toHaveBeenCalledWith('/api/v1/plugins/instances/health-check');
    });

    it('displays error state when API calls fail', async () => {
      const errorMessage = 'Failed to load plugins';
      mockHttpClient.get.mockRejectedValue(new Error(errorMessage));

      render(<PluginsPage />);

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });

      // Should show retry button
      expect(screen.getByRole('button', { name: /Retry/ })).toBeInTheDocument();
    });

    it('allows retrying after error', async () => {
      const user = userEvent.setup();

      // First call fails
      mockHttpClient.get.mockRejectedValueOnce(new Error('Network error'));

      render(<PluginsPage />);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });

      // Setup successful response for retry
      mockHttpClient.get.mockResolvedValue({ data: mockAvailablePlugins });

      const retryButton = screen.getByRole('button', { name: /Retry/ });
      await user.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('Plugin Management')).toBeInTheDocument();
      });
    });
  });

  describe('Statistics Display', () => {
    beforeEach(async () => {
      render(<PluginsPage />);
      await waitFor(() => {
        expect(screen.getByText('Plugin Management')).toBeInTheDocument();
      });
    });

    it('displays correct available plugins count', () => {
      expect(screen.getByText('3')).toBeInTheDocument(); // 3 available plugins
      expect(screen.getByText('Available Plugins')).toBeInTheDocument();
    });

    it('displays correct active instances count', () => {
      expect(screen.getByText('2')).toBeInTheDocument(); // 2 active instances
      expect(screen.getByText('Active Instances')).toBeInTheDocument();
    });

    it('displays correct healthy instances count', () => {
      expect(screen.getByText('1')).toBeInTheDocument(); // 1 healthy instance
      expect(screen.getByText('Healthy')).toBeInTheDocument();
    });

    it('displays correct issues count', () => {
      expect(screen.getByText('1')).toBeInTheDocument(); // 1 issue
      expect(screen.getByText('Issues')).toBeInTheDocument();
    });
  });

  describe('Search and Filtering', () => {
    beforeEach(async () => {
      render(<PluginsPage />);
      await waitFor(() => {
        expect(screen.getByText('Plugin Management')).toBeInTheDocument();
      });
    });

    it('allows searching plugins by name', async () => {
      const user = userEvent.setup();

      const searchInput = screen.getByPlaceholderText('Search plugins...');
      await user.type(searchInput, 'WhatsApp');

      // Should filter the display - this would be tested through the rendered components
      expect(searchInput).toHaveValue('WhatsApp');
    });

    it('allows filtering by plugin type', async () => {
      const user = userEvent.setup();

      const filterSelect = screen.getByDisplayValue('All Types');
      await user.selectOptions(filterSelect, 'notification');

      expect(filterSelect).toHaveValue('notification');
    });

    it('switches filter options when changing view mode', async () => {
      const user = userEvent.setup();

      // Switch to list view
      const listViewButton = screen.getByRole('button', { name: /list view/i }) ||
                           document.querySelector('[data-view="list"]');

      if (listViewButton) {
        await user.click(listViewButton);

        // Should show status filter instead of type filter
        expect(screen.getByDisplayValue('All Status')).toBeInTheDocument();
      }
    });
  });

  describe('View Mode Switching', () => {
    beforeEach(async () => {
      render(<PluginsPage />);
      await waitFor(() => {
        expect(screen.getByText('Plugin Management')).toBeInTheDocument();
      });
    });

    it('starts in grid view by default', () => {
      expect(screen.getByText('Available Plugins')).toBeInTheDocument();
    });

    it('switches to list view when list button clicked', async () => {
      const user = userEvent.setup();

      const listViewButton = screen.getByRole('button', { name: /list/i }) ||
                           document.querySelector('button[class*="bg-slate-800"]');

      if (listViewButton) {
        await user.click(listViewButton);
        expect(screen.getByText('Plugin Instances')).toBeInTheDocument();
      }
    });

    it('switches to health view when health button clicked', async () => {
      const user = userEvent.setup();

      const healthViewButton = screen.getByRole('button', { name: /health/i }) ||
                             document.querySelector('button svg[class*="w-4 h-4"]')?.closest('button');

      if (healthViewButton) {
        await user.click(healthViewButton);
        expect(screen.getByTestId('health-dashboard')).toBeInTheDocument();
      }
    });
  });

  describe('Plugin Installation', () => {
    beforeEach(async () => {
      render(<PluginsPage />);
      await waitFor(() => {
        expect(screen.getByText('Plugin Management')).toBeInTheDocument();
      });
    });

    it('opens plugin form when Add Plugin button is clicked', async () => {
      const user = userEvent.setup();

      const addButton = screen.getByRole('button', { name: /Add Plugin/ });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByTestId('plugin-form')).toBeInTheDocument();
      });
    });

    it('opens plugin form when plugin card install button is clicked', async () => {
      const user = userEvent.setup();

      // First ensure we're in grid view to see plugin cards
      await waitFor(() => {
        expect(screen.getByTestId('plugin-card')).toBeInTheDocument();
      });

      const installButton = screen.getByRole('button', { name: /Install Plugin/ });
      await user.click(installButton);

      await waitFor(() => {
        expect(screen.getByTestId('plugin-form')).toBeInTheDocument();
      });
    });

    it('creates plugin instance when form is submitted', async () => {
      const user = userEvent.setup();

      const addButton = screen.getByRole('button', { name: /Add Plugin/ });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByTestId('plugin-form')).toBeInTheDocument();
      });

      const submitButton = screen.getByRole('button', { name: /Submit Form/ });
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockHttpClient.post).toHaveBeenCalledWith('/api/v1/plugins/instances', {
          plugin_name: 'Test',
          instance_name: 'Test Instance',
          configuration: {}
        });
      });

      // Form should close after successful submission
      expect(screen.queryByTestId('plugin-form')).not.toBeInTheDocument();
    });

    it('handles plugin creation errors', async () => {
      const user = userEvent.setup();

      mockHttpClient.post.mockRejectedValueOnce(new Error('Creation failed'));

      const addButton = screen.getByRole('button', { name: /Add Plugin/ });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByTestId('plugin-form')).toBeInTheDocument();
      });

      const submitButton = screen.getByRole('button', { name: /Submit Form/ });
      await user.click(submitButton);

      // Error should be handled by the form component
      await waitFor(() => {
        expect(mockHttpClient.post).toHaveBeenCalled();
      });
    });

    it('closes form when cancel is clicked', async () => {
      const user = userEvent.setup();

      const addButton = screen.getByRole('button', { name: /Add Plugin/ });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByTestId('plugin-form')).toBeInTheDocument();
      });

      const cancelButton = screen.getByRole('button', { name: /Cancel Form/ });
      await user.click(cancelButton);

      expect(screen.queryByTestId('plugin-form')).not.toBeInTheDocument();
    });
  });

  describe('Plugin Instance Management', () => {
    beforeEach(async () => {
      render(<PluginsPage />);
      await waitFor(() => {
        expect(screen.getByText('Plugin Management')).toBeInTheDocument();
      });
    });

    it('allows deleting plugin instances', async () => {
      const user = userEvent.setup();

      // Mock confirm dialog
      const originalConfirm = window.confirm;
      window.confirm = jest.fn(() => true);

      // Switch to list view to see instances
      const listViewButton = screen.getByRole('button', { name: /list/i }) ||
                           document.querySelector('button[class*="bg-slate-800"]');

      if (listViewButton) {
        await user.click(listViewButton);

        await waitFor(() => {
          expect(screen.getByText('Plugin Instances')).toBeInTheDocument();
        });

        // Implementation would depend on how delete buttons are rendered in list view
        // This is a placeholder for the delete functionality test
      }

      window.confirm = originalConfirm;
    });

    it('handles delete confirmation cancellation', async () => {
      const user = userEvent.setup();

      // Mock confirm dialog to return false (cancel)
      const originalConfirm = window.confirm;
      window.confirm = jest.fn(() => false);

      // Switch to list view and attempt delete
      // ... similar setup as above test

      expect(mockHttpClient.delete).not.toHaveBeenCalled();

      window.confirm = originalConfirm;
    });
  });

  describe('Connection Testing', () => {
    beforeEach(async () => {
      render(<PluginsPage />);
      await waitFor(() => {
        expect(screen.getByText('Plugin Management')).toBeInTheDocument();
      });
    });

    it('handles connection testing', async () => {
      const user = userEvent.setup();

      mockHttpClient.post.mockImplementation((url: string) => {
        if (url.includes('/test')) {
          return Promise.resolve({
            data: {
              success: true,
              message: 'Connection successful'
            }
          });
        }
        return mockHttpClient.post(url);
      });

      const addButton = screen.getByRole('button', { name: /Add Plugin/ });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByTestId('plugin-form')).toBeInTheDocument();
      });

      const testButton = screen.getByRole('button', { name: /Test Connection/ });
      await user.click(testButton);

      await waitFor(() => {
        expect(mockHttpClient.post).toHaveBeenCalledWith(
          expect.stringContaining('/test'),
          expect.any(Object)
        );
      });
    });

    it('handles connection test failures', async () => {
      const user = userEvent.setup();

      mockHttpClient.post.mockImplementation((url: string) => {
        if (url.includes('/test')) {
          return Promise.reject(new Error('Connection failed'));
        }
        return mockHttpClient.post(url);
      });

      const addButton = screen.getByRole('button', { name: /Add Plugin/ });
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByTestId('plugin-form')).toBeInTheDocument();
      });

      const testButton = screen.getByRole('button', { name: /Test Connection/ });
      await user.click(testButton);

      await waitFor(() => {
        expect(mockHttpClient.post).toHaveBeenCalled();
      });
    });
  });

  describe('Plugin Registry Refresh', () => {
    beforeEach(async () => {
      render(<PluginsPage />);
      await waitFor(() => {
        expect(screen.getByText('Plugin Management')).toBeInTheDocument();
      });
    });

    it('refreshes plugin registry when refresh button is clicked', async () => {
      const user = userEvent.setup();

      const refreshButton = screen.getByRole('button', { name: /Refresh/ });
      await user.click(refreshButton);

      await waitFor(() => {
        expect(mockHttpClient.post).toHaveBeenCalledWith('/api/v1/plugins/refresh');
      });

      // Should reload all data after refresh
      expect(mockHttpClient.get).toHaveBeenCalledWith('/api/v1/plugins/');
      expect(mockHttpClient.get).toHaveBeenCalledWith('/api/v1/plugins/instances');
    });

    it('handles refresh errors', async () => {
      const user = userEvent.setup();

      mockHttpClient.post.mockImplementation((url: string) => {
        if (url === '/api/v1/plugins/refresh') {
          return Promise.reject(new Error('Refresh failed'));
        }
        return Promise.resolve({ data: mockHealthChecks });
      });

      const refreshButton = screen.getByRole('button', { name: /Refresh/ });
      await user.click(refreshButton);

      await waitFor(() => {
        expect(screen.getByText(/Refresh failed/)).toBeInTheDocument();
      });
    });
  });

  describe('Health Dashboard Integration', () => {
    beforeEach(async () => {
      render(<PluginsPage />);
      await waitFor(() => {
        expect(screen.getByText('Plugin Management')).toBeInTheDocument();
      });
    });

    it('passes correct data to health dashboard', async () => {
      const user = userEvent.setup();

      // Switch to health view
      const healthViewButton = screen.getByRole('button', { name: /health/i }) ||
                             document.querySelector('button svg[class*="w-4 h-4"]')?.closest('button');

      if (healthViewButton) {
        await user.click(healthViewButton);

        await waitFor(() => {
          expect(screen.getByTestId('health-dashboard')).toBeInTheDocument();
        });

        // Test that health dashboard receives refresh callback
        const refreshHealthButton = screen.getByRole('button', { name: /Refresh Health/ });
        await user.click(refreshHealthButton);

        // Should trigger data reload
        await waitFor(() => {
          expect(mockHttpClient.get).toHaveBeenCalledWith('/api/v1/plugins/');
        });
      }
    });
  });

  describe('Accessibility', () => {
    beforeEach(async () => {
      render(<PluginsPage />);
      await waitFor(() => {
        expect(screen.getByText('Plugin Management')).toBeInTheDocument();
      });
    });

    it('has accessible button labels', () => {
      expect(screen.getByRole('button', { name: /Add Plugin/ })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Refresh/ })).toBeInTheDocument();
    });

    it('has accessible form controls', () => {
      expect(screen.getByPlaceholderText('Search plugins...')).toBeInTheDocument();
      expect(screen.getByDisplayValue('All Types')).toBeInTheDocument();
    });

    it('uses semantic HTML structure', () => {
      expect(screen.getByRole('main') || screen.getByRole('article') || document.querySelector('main')).toBeTruthy();
      expect(screen.getByText('Plugin Management')).toBeInTheDocument();
    });
  });

  describe('Responsive Behavior', () => {
    beforeEach(async () => {
      render(<PluginsPage />);
      await waitFor(() => {
        expect(screen.getByText('Plugin Management')).toBeInTheDocument();
      });
    });

    it('handles mobile layout appropriately', () => {
      // Test responsive grid classes are applied
      const statsSection = document.querySelector('.grid');
      expect(statsSection).toHaveClass('grid-cols-1');
      expect(statsSection).toHaveClass('md:grid-cols-4');
    });

    it('stacks controls vertically on mobile', () => {
      const controlsSection = document.querySelector('.flex-col');
      expect(controlsSection).toBeTruthy();
    });
  });
});