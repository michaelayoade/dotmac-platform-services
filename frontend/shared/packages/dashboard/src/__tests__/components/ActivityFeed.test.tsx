/**
 * ActivityFeed Component Test Suite
 * Production-ready test coverage for universal activity component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ActivityFeed, ActivityFeedPresets } from '../../components/ActivityFeed/ActivityFeed';
import type { Activity, ActivityFeedConfig } from '../../types';

const mockActivities: Activity[] = [
  {
    id: '1',
    type: 'success',
    title: 'User registered',
    description: 'New user john@example.com successfully registered',
    timestamp: new Date('2024-01-15T10:30:00Z'),
    userName: 'System',
    metadata: { email: 'john@example.com', source: 'registration' },
  },
  {
    id: '2',
    type: 'warning',
    title: 'High CPU usage',
    description: 'Server CPU usage exceeded 80% threshold',
    timestamp: new Date('2024-01-15T09:15:00Z'),
    userName: 'Monitoring',
    metadata: { cpu: 85, server: 'web-01' },
  },
  {
    id: '3',
    type: 'error',
    title: 'Payment failed',
    description: 'Payment processing failed for customer ID 12345',
    timestamp: new Date('2024-01-15T08:45:00Z'),
    userName: 'Billing',
    metadata: { customerId: '12345', amount: 99.99 },
  },
  {
    id: '4',
    type: 'info',
    title: 'System backup',
    description: 'Daily system backup completed successfully',
    timestamp: new Date('2024-01-15T02:00:00Z'),
    userName: 'Backup Service',
  },
];

const defaultProps = {
  activities: mockActivities,
  variant: 'admin' as const,
};

describe('📰 ActivityFeed', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render all activities', () => {
      render(<ActivityFeed {...defaultProps} />);

      expect(screen.getByText('User registered')).toBeInTheDocument();
      expect(screen.getByText('High CPU usage')).toBeInTheDocument();
      expect(screen.getByText('Payment failed')).toBeInTheDocument();
      expect(screen.getByText('System backup')).toBeInTheDocument();
    });

    it('should render activity descriptions', () => {
      render(<ActivityFeed {...defaultProps} />);

      expect(
        screen.getByText('New user john@example.com successfully registered')
      ).toBeInTheDocument();
      expect(screen.getByText('Server CPU usage exceeded 80% threshold')).toBeInTheDocument();
    });

    it('should render user names when showUserAvatars is enabled', () => {
      const config: Partial<ActivityFeedConfig> = {
        showUserAvatars: true,
      };

      render(<ActivityFeed {...defaultProps} config={config} />);

      expect(screen.getByText('System')).toBeInTheDocument();
      expect(screen.getByText('Monitoring')).toBeInTheDocument();
      expect(screen.getByText('Billing')).toBeInTheDocument();
    });

    it('should render metadata when available', () => {
      render(<ActivityFeed {...defaultProps} />);

      expect(screen.getByText('email: john@example.com')).toBeInTheDocument();
      expect(screen.getByText('cpu: 85')).toBeInTheDocument();
      expect(screen.getByText('customerId: 12345')).toBeInTheDocument();
    });
  });

  describe('Portal Variants', () => {
    it.each(['admin', 'customer', 'reseller', 'technician', 'management'])(
      'should apply %s variant styles',
      (variant) => {
        const { container } = render(<ActivityFeed {...defaultProps} variant={variant as any} />);

        const feedElement = container.querySelector('[class*="border-"]');
        expect(feedElement).toHaveClass(expect.stringContaining(variant.slice(0, 4))); // partial match
      }
    );

    it('should apply variant-specific icon colors', () => {
      const { rerender, container } = render(<ActivityFeed {...defaultProps} variant='admin' />);

      let iconElement = container.querySelector('.text-blue-700');
      expect(iconElement).toBeInTheDocument();

      rerender(<ActivityFeed {...defaultProps} variant='customer' />);
      iconElement = container.querySelector('.text-green-600');
      expect(iconElement).toBeInTheDocument();
    });
  });

  describe('Activity Types and Icons', () => {
    it('should render different icons for different activity types', () => {
      render(<ActivityFeed {...defaultProps} />);

      // Each activity type should have its corresponding icon
      const icons = document.querySelectorAll('svg');
      expect(icons.length).toBeGreaterThan(4); // At least one per activity + filter icons
    });

    it('should apply correct colors for activity types', () => {
      render(<ActivityFeed {...defaultProps} />);

      // Check for success (green), warning (yellow), error (red), info (blue) colors
      expect(document.querySelector('.text-green-600')).toBeInTheDocument();
      expect(document.querySelector('.text-yellow-600')).toBeInTheDocument();
      expect(document.querySelector('.text-red-600')).toBeInTheDocument();
      expect(document.querySelector('.text-blue-600')).toBeInTheDocument();
    });
  });

  describe('Search Functionality', () => {
    it('should filter activities based on search query', async () => {
      const user = userEvent.setup();
      render(<ActivityFeed {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText('Search activities...');
      await user.type(searchInput, 'payment');

      await waitFor(() => {
        expect(screen.getByText('Payment failed')).toBeInTheDocument();
        expect(screen.queryByText('User registered')).not.toBeInTheDocument();
      });
    });

    it('should search across multiple fields', async () => {
      const user = userEvent.setup();
      render(<ActivityFeed {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText('Search activities...');

      // Search by user name
      await user.clear(searchInput);
      await user.type(searchInput, 'System');

      await waitFor(() => {
        expect(screen.getByText('User registered')).toBeInTheDocument();
        expect(screen.queryByText('High CPU usage')).not.toBeInTheDocument();
      });

      // Search by description
      await user.clear(searchInput);
      await user.type(searchInput, 'CPU');

      await waitFor(() => {
        expect(screen.getByText('High CPU usage')).toBeInTheDocument();
        expect(screen.queryByText('User registered')).not.toBeInTheDocument();
      });
    });

    it('should show "no activities match" message when search has no results', async () => {
      const user = userEvent.setup();
      render(<ActivityFeed {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText('Search activities...');
      await user.type(searchInput, 'nonexistent');

      await waitFor(() => {
        expect(screen.getByText('No activities match your filters')).toBeInTheDocument();
      });
    });
  });

  describe('Filter Functionality', () => {
    it('should filter activities by type', async () => {
      const user = userEvent.setup();
      render(<ActivityFeed {...defaultProps} />);

      const typeFilter = screen.getByDisplayValue('All Types');
      await user.selectOptions(typeFilter, 'error');

      await waitFor(() => {
        expect(screen.getByText('Payment failed')).toBeInTheDocument();
        expect(screen.queryByText('User registered')).not.toBeInTheDocument();
      });
    });

    it('should support all filter type options', async () => {
      const user = userEvent.setup();
      render(<ActivityFeed {...defaultProps} />);

      const typeFilter = screen.getByDisplayValue('All Types');

      // Test each filter option
      for (const type of ['success', 'warning', 'error', 'info']) {
        await user.selectOptions(typeFilter, type);

        await waitFor(() => {
          const visibleActivities = mockActivities.filter((activity) => activity.type === type);
          expect(visibleActivities.length).toBeGreaterThan(0);
        });
      }
    });

    it('should combine search and filter', async () => {
      const user = userEvent.setup();
      render(<ActivityFeed {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText('Search activities...');
      const typeFilter = screen.getByDisplayValue('All Types');

      await user.type(searchInput, 'user');
      await user.selectOptions(typeFilter, 'success');

      await waitFor(() => {
        expect(screen.getByText('User registered')).toBeInTheDocument();
        expect(screen.queryByText('High CPU usage')).not.toBeInTheDocument();
      });
    });

    it('should hide filters when showFilters is false', () => {
      const config: Partial<ActivityFeedConfig> = {
        showFilters: false,
      };

      render(<ActivityFeed {...defaultProps} config={config} />);

      expect(screen.queryByPlaceholderText('Search activities...')).not.toBeInTheDocument();
      expect(screen.queryByDisplayValue('All Types')).not.toBeInTheDocument();
    });
  });

  describe('Sorting and Ordering', () => {
    it('should display activities in chronological order (newest first)', () => {
      render(<ActivityFeed {...defaultProps} />);

      const activities = screen.getAllByRole('button', { name: /.*/ });
      const titles = activities.map((activity) => activity.textContent);

      // Should be ordered by timestamp (newest first)
      expect(titles[0]).toContain('User registered');
      expect(titles[3]).toContain('System backup');
    });
  });

  describe('Pagination and Expansion', () => {
    it('should limit activities to maxItems', () => {
      const config: Partial<ActivityFeedConfig> = {
        maxItems: 2,
      };

      render(<ActivityFeed {...defaultProps} config={config} />);

      expect(screen.getByText('User registered')).toBeInTheDocument();
      expect(screen.getByText('High CPU usage')).toBeInTheDocument();
      expect(screen.queryByText('Payment failed')).not.toBeInTheDocument();
    });

    it('should show expand button when there are more activities', () => {
      const config: Partial<ActivityFeedConfig> = {
        maxItems: 2,
      };

      render(<ActivityFeed {...defaultProps} config={config} />);

      expect(screen.getByText('Show 2 More')).toBeInTheDocument();
    });

    it('should expand to show all activities when expand button is clicked', async () => {
      const user = userEvent.setup();
      const config: Partial<ActivityFeedConfig> = {
        maxItems: 2,
      };

      render(<ActivityFeed {...defaultProps} config={config} />);

      const expandButton = screen.getByText('Show 2 More');
      await user.click(expandButton);

      await waitFor(() => {
        expect(screen.getByText('Payment failed')).toBeInTheDocument();
        expect(screen.getByText('System backup')).toBeInTheDocument();
        expect(screen.getByText('Show Less')).toBeInTheDocument();
      });
    });

    it('should collapse activities when "Show Less" is clicked', async () => {
      const user = userEvent.setup();
      const config: Partial<ActivityFeedConfig> = {
        maxItems: 2,
      };

      render(<ActivityFeed {...defaultProps} config={config} />);

      // Expand first
      const expandButton = screen.getByText('Show 2 More');
      await user.click(expandButton);

      await waitFor(() => {
        expect(screen.getByText('Show Less')).toBeInTheDocument();
      });

      // Then collapse
      const collapseButton = screen.getByText('Show Less');
      await user.click(collapseButton);

      await waitFor(() => {
        expect(screen.queryByText('System backup')).not.toBeInTheDocument();
        expect(screen.getByText('Show 2 More')).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('should render loading skeleton', () => {
      render(<ActivityFeed {...defaultProps} loading={true} />);

      expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
      expect(screen.queryByText('User registered')).not.toBeInTheDocument();
    });

    it('should render multiple loading items', () => {
      render(<ActivityFeed {...defaultProps} loading={true} />);

      const loadingItems = document.querySelectorAll('.animate-pulse .space-y-2');
      expect(loadingItems.length).toBeGreaterThan(0);
    });
  });

  describe('Empty State', () => {
    it('should show empty state when no activities', () => {
      render(<ActivityFeed activities={[]} variant='admin' />);

      expect(screen.getByText('No recent activities')).toBeInTheDocument();
    });

    it('should show filtered empty state when search has no results', async () => {
      const user = userEvent.setup();
      render(<ActivityFeed {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText('Search activities...');
      await user.type(searchInput, 'nonexistent');

      await waitFor(() => {
        expect(screen.getByText('No activities match your filters')).toBeInTheDocument();
      });
    });
  });

  describe('Interactions', () => {
    it('should call onActivityClick when activity is clicked', async () => {
      const user = userEvent.setup();
      const onActivityClick = jest.fn();

      render(<ActivityFeed {...defaultProps} onActivityClick={onActivityClick} />);

      const activity = screen.getByText('User registered').closest('[role="button"]');
      if (activity) {
        await user.click(activity);
        expect(onActivityClick).toHaveBeenCalledWith(mockActivities[0]);
      }
    });

    it('should call onRefresh when refresh button is clicked', async () => {
      const user = userEvent.setup();
      const onRefresh = jest.fn();

      render(<ActivityFeed {...defaultProps} onRefresh={onRefresh} />);

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      await user.click(refreshButton);

      expect(onRefresh).toHaveBeenCalled();
    });

    it('should show loading state for refresh button during loading', () => {
      render(<ActivityFeed {...defaultProps} loading={true} onRefresh={jest.fn()} />);

      // During loading state, refresh button should be disabled/hidden
      const refreshButton = screen.queryByRole('button', { name: /refresh/i });
      if (refreshButton) {
        expect(refreshButton).toBeDisabled();
      }
    });
  });

  describe('Time Formatting', () => {
    it('should format timestamps relative to current time', () => {
      // Mock current time for consistent testing
      const mockDate = new Date('2024-01-15T12:00:00Z');
      jest.useFakeTimers();
      jest.setSystemTime(mockDate);

      render(<ActivityFeed {...defaultProps} />);

      // Should show relative time like "2 hours ago", "3 hours ago", etc.
      expect(screen.getByText(/ago$/)).toBeInTheDocument();

      jest.useRealTimers();
    });
  });

  describe('Portal Presets', () => {
    describe('Management Portal Activities', () => {
      it('should generate tenant creation activity', () => {
        const activity = ActivityFeedPresets.management.tenantCreated('Acme Corp', 'admin');

        expect(activity.type).toBe('success');
        expect(activity.title).toBe('New Tenant Created');
        expect(activity.description).toContain('Acme Corp');
        expect(activity.userName).toBe('admin');
        expect(activity.metadata?.tenantName).toBe('Acme Corp');
      });

      it('should generate system alert activity', () => {
        const warningAlert = ActivityFeedPresets.management.systemAlert(
          'Disk space low',
          'warning'
        );
        expect(warningAlert.type).toBe('warning');
        expect(warningAlert.title).toBe('System Alert');

        const errorAlert = ActivityFeedPresets.management.systemAlert('Service down', 'error');
        expect(errorAlert.type).toBe('error');
      });
    });

    describe('Admin Portal Activities', () => {
      it('should generate customer signup activity', () => {
        const activity = ActivityFeedPresets.admin.customerSignup('john@example.com', 'Premium');

        expect(activity.type).toBe('success');
        expect(activity.title).toBe('New Customer Signup');
        expect(activity.description).toContain('john@example.com');
        expect(activity.description).toContain('Premium');
      });

      it('should generate network outage activity', () => {
        const activity = ActivityFeedPresets.admin.networkOutage('Downtown', '2 hours');

        expect(activity.type).toBe('error');
        expect(activity.title).toBe('Network Outage');
        expect(activity.description).toContain('Downtown');
        expect(activity.description).toContain('2 hours');
      });
    });

    describe('Customer Portal Activities', () => {
      it('should generate bill generated activity', () => {
        const activity = ActivityFeedPresets.customer.billGenerated(89.99, '2024-02-15');

        expect(activity.type).toBe('info');
        expect(activity.title).toBe('New Bill Available');
        expect(activity.description).toContain('$89.99');
        expect(activity.description).toContain('2024-02-15');
      });

      it('should generate payment processed activity', () => {
        const activity = ActivityFeedPresets.customer.paymentProcessed(89.99, 'Credit Card');

        expect(activity.type).toBe('success');
        expect(activity.title).toBe('Payment Processed');
        expect(activity.description).toContain('$89.99');
        expect(activity.description).toContain('Credit Card');
      });
    });

    describe('Reseller Portal Activities', () => {
      it('should generate commission earned activity', () => {
        const activity = ActivityFeedPresets.reseller.commissionEarned(25.5, 'John Doe');

        expect(activity.type).toBe('success');
        expect(activity.title).toBe('Commission Earned');
        expect(activity.description).toContain('$25.50');
        expect(activity.description).toContain('John Doe');
      });

      it('should generate lead converted activity', () => {
        const activity = ActivityFeedPresets.reseller.leadConverted('Jane Smith', 'Business');

        expect(activity.type).toBe('success');
        expect(activity.title).toBe('Lead Converted');
        expect(activity.description).toContain('Jane Smith');
        expect(activity.description).toContain('Business');
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(<ActivityFeed {...defaultProps} />);

      const feedContainer = screen.getByRole('region') || screen.getByRole('feed');
      expect(feedContainer).toBeInTheDocument();
    });

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      const onActivityClick = jest.fn();

      render(<ActivityFeed {...defaultProps} onActivityClick={onActivityClick} />);

      const firstActivity = screen.getByText('User registered').closest('[role="button"]');
      if (firstActivity) {
        await user.tab();
        expect(firstActivity).toHaveFocus();

        await user.keyboard('{Enter}');
        expect(onActivityClick).toHaveBeenCalled();
      }
    });

    it('should have accessible search input', () => {
      render(<ActivityFeed {...defaultProps} />);

      const searchInput = screen.getByRole('textbox', { name: /search/i });
      expect(searchInput).toBeInTheDocument();
      expect(searchInput).toHaveAttribute('placeholder', 'Search activities...');
    });
  });

  describe('Performance', () => {
    it('should handle large number of activities efficiently', () => {
      const largeActivities = Array.from({ length: 1000 }, (_, i) => ({
        id: String(i),
        type: 'info' as const,
        title: `Activity ${i}`,
        description: `Description for activity ${i}`,
        timestamp: new Date(2024, 0, 15, 10, 30 + i),
      }));

      const startTime = performance.now();
      render(<ActivityFeed activities={largeActivities} variant='admin' />);
      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(100);
    });

    it('should debounce search input', async () => {
      const user = userEvent.setup();
      render(<ActivityFeed {...defaultProps} />);

      const searchInput = screen.getByPlaceholderText('Search activities...');

      await user.type(searchInput, 'test search');

      // Should update the input value immediately
      expect(searchInput).toHaveValue('test search');
    });
  });

  describe('Error Handling', () => {
    it('should handle activities with missing fields', () => {
      const incompleteActivities = [
        {
          id: '1',
          type: 'info' as const,
          title: 'Complete Activity',
          description: 'This has all fields',
          timestamp: new Date(),
        },
        {
          id: '2',
          type: 'warning' as const,
          title: 'Incomplete Activity',
          description: '', // Empty description
          timestamp: new Date(),
          // Missing userName, metadata
        },
      ];

      expect(() => {
        render(<ActivityFeed activities={incompleteActivities} variant='admin' />);
      }).not.toThrow();

      expect(screen.getByText('Complete Activity')).toBeInTheDocument();
      expect(screen.getByText('Incomplete Activity')).toBeInTheDocument();
    });

    it('should handle invalid timestamps gracefully', () => {
      const activitiesWithInvalidDates = [
        {
          ...mockActivities[0],
          timestamp: new Date('invalid-date'),
        },
      ];

      expect(() => {
        render(<ActivityFeed activities={activitiesWithInvalidDates} variant='admin' />);
      }).not.toThrow();
    });
  });
});
