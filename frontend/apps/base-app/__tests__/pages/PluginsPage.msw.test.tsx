/**
 * PluginsPage Tests with MSW
 * Tests the plugins management page using Mock Service Worker for API mocking
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { server } from '../mocks/server';
import { mockAvailablePlugins, mockPluginInstances, mockHealthChecks } from '../mocks/handlers';
import PluginsPage from '../../app/dashboard/settings/plugins/page';

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

describe('PluginsPage with MSW', () => {
  describe('Page Loading', () => {
    it('shows loading state initially', async () => {
      // Delay the API response to test loading state
      server.use(
        http.get('*/api/v1/plugins/', async () => {
          await new Promise(resolve => setTimeout(resolve, 100));
          return HttpResponse.json(mockAvailablePlugins);
        })
      );

      render(<PluginsPage />);

      expect(screen.getByText('Loading plugins...')).toBeInTheDocument();

      // Wait for loading to complete
      await waitFor(() => {
        expect(screen.queryByText('Loading plugins...')).not.toBeInTheDocument();
      }, { timeout: 3000 });
    });

    it('loads and displays plugin data on mount', async () => {
      render(<PluginsPage />);

      await waitFor(() => {
        expect(screen.getByText('Plugin Management')).toBeInTheDocument();
      });

      // Should have made the expected API calls via MSW
      expect(screen.getByText('Plugin Management')).toBeInTheDocument();
    });

    it('displays error state when API calls fail', async () => {
      const errorMessage = 'Failed to load plugins';

      server.use(
        http.get('*/api/v1/plugins/', () => {
          return HttpResponse.json(
            { error: errorMessage },
            { status: 500 }
          );
        })
      );

      render(<PluginsPage />);

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });

      // Should show retry button
      expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument();
    });

    it('allows retrying after error', async () => {
      const user = userEvent.setup();
      let callCount = 0;

      // First call fails, second succeeds
      server.use(
        http.get('*/api/v1/plugins/', () => {
          callCount++;
          if (callCount === 1) {
            return HttpResponse.json(
              { error: 'Network error' },
              { status: 500 }
            );
          }
          return HttpResponse.json(mockAvailablePlugins);
        })
      );

      render(<PluginsPage />);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });

      const retryButton = screen.getByRole('button', { name: /Retry/i });

      await act(async () => {
        await user.click(retryButton);
      });

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

      await act(async () => {
        await user.type(searchInput, 'WhatsApp');
      });

      expect(searchInput).toHaveValue('WhatsApp');
    });

    it('allows filtering by plugin type', async () => {
      const user = userEvent.setup();

      const filterSelect = screen.getByDisplayValue('All Types');

      await act(async () => {
        await user.selectOptions(filterSelect, 'notification');
      });

      expect(filterSelect).toHaveValue('notification');
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

      const addButton = screen.getByRole('button', { name: /Add Plugin/i });

      await act(async () => {
        await user.click(addButton);
      });

      await waitFor(() => {
        expect(screen.getByTestId('plugin-form')).toBeInTheDocument();
      });
    });

    it('creates plugin instance when form is submitted', async () => {
      const user = userEvent.setup();

      const addButton = screen.getByRole('button', { name: /Add Plugin/i });

      await act(async () => {
        await user.click(addButton);
      });

      await waitFor(() => {
        expect(screen.getByTestId('plugin-form')).toBeInTheDocument();
      });

      const submitButton = screen.getByRole('button', { name: /Submit Form/i });

      await act(async () => {
        await user.click(submitButton);
      });

      // Form should close after successful submission
      await waitFor(() => {
        expect(screen.queryByTestId('plugin-form')).not.toBeInTheDocument();
      });
    });

    it('closes form when cancel is clicked', async () => {
      const user = userEvent.setup();

      const addButton = screen.getByRole('button', { name: /Add Plugin/i });

      await act(async () => {
        await user.click(addButton);
      });

      await waitFor(() => {
        expect(screen.getByTestId('plugin-form')).toBeInTheDocument();
      });

      const cancelButton = screen.getByRole('button', { name: /Cancel Form/i });

      await act(async () => {
        await user.click(cancelButton);
      });

      expect(screen.queryByTestId('plugin-form')).not.toBeInTheDocument();
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

      const refreshButton = screen.getByRole('button', { name: /Refresh/i });

      await act(async () => {
        await user.click(refreshButton);
      });

      // Should trigger data reload
      await waitFor(() => {
        expect(screen.getByText('Plugin Management')).toBeInTheDocument();
      });
    });

    it('handles refresh errors', async () => {
      const user = userEvent.setup();

      server.use(
        http.post('*/api/v1/plugins/refresh', () => {
          return HttpResponse.json(
            { error: 'Refresh failed' },
            { status: 500 }
          );
        })
      );

      const refreshButton = screen.getByRole('button', { name: /Refresh/i });

      await act(async () => {
        await user.click(refreshButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/Refresh failed/i)).toBeInTheDocument();
      });
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
      expect(screen.getByRole('button', { name: /Add Plugin/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Refresh/i })).toBeInTheDocument();
    });

    it('has accessible form controls', () => {
      expect(screen.getByPlaceholderText('Search plugins...')).toBeInTheDocument();
      expect(screen.getByDisplayValue('All Types')).toBeInTheDocument();
    });
  });
});
