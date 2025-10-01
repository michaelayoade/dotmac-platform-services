import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// Mock the http-client
const mockHttpClient = {
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
};

jest.mock('@dotmac/http-client', () => ({
  httpClient: mockHttpClient,
}));

// Mock child components
jest.mock('../../app/dashboard/settings/plugins/components/PluginForm', () => ({
  PluginForm: ({ onSubmit, onCancel, onTestConnection }: any) => (
    <div data-testid="plugin-form">
      <button onClick={() => onSubmit({ instanceName: 'test', pluginName: 'test', config: {} })}>
        Submit Form
      </button>
      <button onClick={onCancel}>Cancel Form</button>
      <button onClick={() => onTestConnection({ instanceName: 'test', pluginName: 'test', config: {} })}>
        Test Connection
      </button>
    </div>
  ),
}));

jest.mock('../../app/dashboard/settings/plugins/components/PluginCard', () => ({
  PluginCard: ({ plugin, onInstall, onConfigure, onDelete }: any) => (
    <div data-testid="plugin-card">
      <h3>{plugin.name}</h3>
      <button onClick={() => onInstall(plugin)}>Install</button>
      <button onClick={() => onConfigure(plugin)}>Configure</button>
      <button onClick={() => onDelete(plugin)}>Delete</button>
    </div>
  ),
}));

jest.mock('../../app/dashboard/settings/plugins/components/PluginHealthDashboard', () => ({
  PluginHealthDashboard: ({ instances }: any) => (
    <div data-testid="health-dashboard">
      Health Dashboard - {instances.length} instances
    </div>
  ),
}));

const mockAvailablePlugins = [
  { name: 'WhatsApp Business', type: 'integration' },
  { name: 'Slack Integration', type: 'integration' },
  { name: 'Payment Gateway', type: 'integration' }
];

const mockActiveInstances = [
  { id: '1', instanceName: 'WhatsApp Prod', pluginName: 'WhatsApp Business', status: 'active' },
  { id: '2', instanceName: 'Slack Dev', pluginName: 'Slack Integration', status: 'inactive' }
];

describe('PluginsPage Coverage Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockHttpClient.get.mockResolvedValue({ data: mockAvailablePlugins });
    mockHttpClient.post.mockResolvedValue({ data: mockActiveInstances });
  });

  it('handles refresh action', async () => {
    const PluginsPage = (await import('../../app/dashboard/settings/plugins/page')).default;
    const user = userEvent.setup();

    render(<PluginsPage />);

    await waitFor(() => {
      expect(screen.getByText('Plugin Management')).toBeInTheDocument();
    });

    const refreshButton = screen.getByRole('button', { name: /Refresh/ });
    await user.click(refreshButton);

    expect(mockHttpClient.get).toHaveBeenCalledTimes(2); // Initial + refresh
    expect(mockHttpClient.post).toHaveBeenCalledTimes(2); // Initial + refresh
  });

  it('handles add plugin action', async () => {
    const PluginsPage = (await import('../../app/dashboard/settings/plugins/page')).default;
    const user = userEvent.setup();

    render(<PluginsPage />);

    await waitFor(() => {
      expect(screen.getByText('Plugin Management')).toBeInTheDocument();
    });

    const addButton = screen.getByRole('button', { name: /Add Plugin/ });
    await user.click(addButton);

    expect(screen.getByTestId('plugin-form')).toBeInTheDocument();
  });

  it('handles plugin installation', async () => {
    const PluginsPage = (await import('../../app/dashboard/settings/plugins/page')).default;
    const user = userEvent.setup();

    mockHttpClient.put.mockResolvedValue({ data: { success: true } });

    render(<PluginsPage />);

    await waitFor(() => {
      expect(screen.getByText('WhatsApp Business')).toBeInTheDocument();
    });

    const installButton = screen.getByText('Install');
    await user.click(installButton);

    expect(screen.getByTestId('plugin-form')).toBeInTheDocument();
  });

  it('handles plugin configuration', async () => {
    const PluginsPage = (await import('../../app/dashboard/settings/plugins/page')).default;
    const user = userEvent.setup();

    render(<PluginsPage />);

    await waitFor(() => {
      expect(screen.getByText('WhatsApp Business')).toBeInTheDocument();
    });

    const configureButton = screen.getByText('Configure');
    await user.click(configureButton);

    expect(screen.getByTestId('plugin-form')).toBeInTheDocument();
  });

  it('handles plugin deletion with confirmation', async () => {
    const PluginsPage = (await import('../../app/dashboard/settings/plugins/page')).default;
    const user = userEvent.setup();

    mockHttpClient.delete.mockResolvedValue({ data: { success: true } });

    // Mock window.confirm to return true
    const originalConfirm = window.confirm;
    window.confirm = jest.fn().mockReturnValue(true);

    render(<PluginsPage />);

    await waitFor(() => {
      expect(screen.getByText('WhatsApp Business')).toBeInTheDocument();
    });

    const deleteButton = screen.getByText('Delete');
    await user.click(deleteButton);

    await waitFor(() => {
      expect(mockHttpClient.delete).toHaveBeenCalled();
    });

    window.confirm = originalConfirm;
  });

  it('handles plugin deletion cancellation', async () => {
    const PluginsPage = (await import('../../app/dashboard/settings/plugins/page')).default;
    const user = userEvent.setup();

    // Mock window.confirm to return false
    const originalConfirm = window.confirm;
    window.confirm = jest.fn().mockReturnValue(false);

    render(<PluginsPage />);

    await waitFor(() => {
      expect(screen.getByText('WhatsApp Business')).toBeInTheDocument();
    });

    const deleteButton = screen.getByText('Delete');
    await user.click(deleteButton);

    expect(mockHttpClient.delete).not.toHaveBeenCalled();

    window.confirm = originalConfirm;
  });

  it('handles form submission success', async () => {
    const PluginsPage = (await import('../../app/dashboard/settings/plugins/page')).default;
    const user = userEvent.setup();

    mockHttpClient.put.mockResolvedValue({ data: { success: true } });

    render(<PluginsPage />);

    await waitFor(() => {
      expect(screen.getByText('Plugin Management')).toBeInTheDocument();
    });

    // Open form
    const addButton = screen.getByRole('button', { name: /Add Plugin/ });
    await user.click(addButton);

    // Submit form
    const submitButton = screen.getByText('Submit Form');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockHttpClient.put).toHaveBeenCalled();
    });
  });

  it('handles form submission error', async () => {
    const PluginsPage = (await import('../../app/dashboard/settings/plugins/page')).default;
    const user = userEvent.setup();

    mockHttpClient.put.mockRejectedValue(new Error('Submission failed'));

    render(<PluginsPage />);

    await waitFor(() => {
      expect(screen.getByText('Plugin Management')).toBeInTheDocument();
    });

    // Open form
    const addButton = screen.getByRole('button', { name: /Add Plugin/ });
    await user.click(addButton);

    // Submit form
    const submitButton = screen.getByText('Submit Form');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/Submission failed/)).toBeInTheDocument();
    });
  });

  it('handles form cancellation', async () => {
    const PluginsPage = (await import('../../app/dashboard/settings/plugins/page')).default;
    const user = userEvent.setup();

    render(<PluginsPage />);

    await waitFor(() => {
      expect(screen.getByText('Plugin Management')).toBeInTheDocument();
    });

    // Open form
    const addButton = screen.getByRole('button', { name: /Add Plugin/ });
    await user.click(addButton);

    // Cancel form
    const cancelButton = screen.getByText('Cancel Form');
    await user.click(cancelButton);

    expect(screen.queryByTestId('plugin-form')).not.toBeInTheDocument();
  });

  it('handles test connection success', async () => {
    const PluginsPage = (await import('../../app/dashboard/settings/plugins/page')).default;
    const user = userEvent.setup();

    mockHttpClient.post.mockResolvedValue({ data: { success: true } });

    render(<PluginsPage />);

    await waitFor(() => {
      expect(screen.getByText('Plugin Management')).toBeInTheDocument();
    });

    // Open form
    const addButton = screen.getByRole('button', { name: /Add Plugin/ });
    await user.click(addButton);

    // Test connection
    const testButton = screen.getByText('Test Connection');
    await user.click(testButton);

    await waitFor(() => {
      expect(mockHttpClient.post).toHaveBeenCalledWith(
        '/api/plugins/test-connection',
        expect.any(Object)
      );
    });
  });

  it('handles test connection error', async () => {
    const PluginsPage = (await import('../../app/dashboard/settings/plugins/page')).default;
    const user = userEvent.setup();

    mockHttpClient.post.mockRejectedValue(new Error('Connection test failed'));

    render(<PluginsPage />);

    await waitFor(() => {
      expect(screen.getByText('Plugin Management')).toBeInTheDocument();
    });

    // Open form
    const addButton = screen.getByRole('button', { name: /Add Plugin/ });
    await user.click(addButton);

    // Test connection
    const testButton = screen.getByText('Test Connection');
    await user.click(testButton);

    await waitFor(() => {
      expect(screen.getByText(/Connection test failed/)).toBeInTheDocument();
    });
  });

  it('handles retry after error', async () => {
    const PluginsPage = (await import('../../app/dashboard/settings/plugins/page')).default;
    const user = userEvent.setup();

    // First call fails, second succeeds
    mockHttpClient.get
      .mockRejectedValueOnce(new Error('API Error'))
      .mockResolvedValueOnce({ data: mockAvailablePlugins });

    render(<PluginsPage />);

    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument();
    });

    const retryButton = screen.getByRole('button', { name: /Retry/ });
    await user.click(retryButton);

    await waitFor(() => {
      expect(screen.getByText('Plugin Management')).toBeInTheDocument();
    });
  });

  it('displays statistics correctly', async () => {
    const PluginsPage = (await import('../../app/dashboard/settings/plugins/page')).default;

    render(<PluginsPage />);

    await waitFor(() => {
      expect(screen.getByText('3')).toBeInTheDocument(); // Available plugins count
      expect(screen.getByText('2')).toBeInTheDocument(); // Active instances count
    });
  });

  it('handles delete operation error', async () => {
    const PluginsPage = (await import('../../app/dashboard/settings/plugins/page')).default;
    const user = userEvent.setup();

    mockHttpClient.delete.mockRejectedValue(new Error('Delete failed'));

    // Mock window.confirm to return true
    const originalConfirm = window.confirm;
    window.confirm = jest.fn().mockReturnValue(true);

    render(<PluginsPage />);

    await waitFor(() => {
      expect(screen.getByText('WhatsApp Business')).toBeInTheDocument();
    });

    const deleteButton = screen.getByText('Delete');
    await user.click(deleteButton);

    await waitFor(() => {
      expect(screen.getByText(/Delete failed/)).toBeInTheDocument();
    });

    window.confirm = originalConfirm;
  });
});