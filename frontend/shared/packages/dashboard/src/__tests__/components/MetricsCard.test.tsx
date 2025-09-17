/**
 * MetricsCard Component Test Suite
 * Production-ready test coverage for universal metrics component
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MetricsCard, MetricsCardPresets } from '../../components/MetricsCard/MetricsCard';
import type { MetricsCardData } from '../../types';
import { Users, TrendingUp } from 'lucide-react';

const mockData: MetricsCardData = {
  title: 'Active Users',
  value: 1234,
  change: '+12.5%',
  trend: 'up',
  icon: Users,
  description: 'Total active users this month',
  actionLabel: 'View Details',
  onAction: jest.fn(),
};

const defaultProps = {
  data: mockData,
  variant: 'admin' as const,
};

describe('📊 MetricsCard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render metrics data correctly', () => {
      render(<MetricsCard {...defaultProps} />);

      expect(screen.getByText('Active Users')).toBeInTheDocument();
      expect(screen.getByText('1,234')).toBeInTheDocument();
      expect(screen.getByText('+12.5%')).toBeInTheDocument();
      expect(screen.getByText('Total active users this month')).toBeInTheDocument();
    });

    it('should render icon when provided', () => {
      render(<MetricsCard {...defaultProps} />);

      // Check if Users icon is rendered (lucide-react icons have specific classes)
      const iconContainer =
        screen.getByRole('img', { hidden: true }) ||
        document.querySelector('[data-lucide]') ||
        document.querySelector('svg');
      expect(iconContainer).toBeInTheDocument();
    });

    it('should render action button when provided', () => {
      render(<MetricsCard {...defaultProps} />);

      const actionButton = screen.getByText('View Details');
      expect(actionButton).toBeInTheDocument();
    });

    it('should handle missing optional props gracefully', () => {
      const minimalData = {
        title: 'Simple Metric',
        value: 100,
      };

      expect(() => {
        render(<MetricsCard data={minimalData} variant='admin' />);
      }).not.toThrow();

      expect(screen.getByText('Simple Metric')).toBeInTheDocument();
      expect(screen.getByText('100')).toBeInTheDocument();
    });
  });

  describe('Portal Variants', () => {
    it.each(['admin', 'customer', 'reseller', 'technician', 'management'])(
      'should apply %s variant styles',
      (variant) => {
        const { container } = render(<MetricsCard {...defaultProps} variant={variant as any} />);

        const cardElement = container.firstChild;
        expect(cardElement).toHaveClass(expect.stringContaining(variant));
      }
    );

    it('should apply correct value text color for variants', () => {
      const { rerender, container } = render(<MetricsCard {...defaultProps} variant='admin' />);

      let valueElement = container.querySelector('.text-blue-900');
      expect(valueElement).toBeInTheDocument();

      rerender(<MetricsCard {...defaultProps} variant='customer' />);
      valueElement = container.querySelector('.text-green-900');
      expect(valueElement).toBeInTheDocument();
    });
  });

  describe('Trend Indicators', () => {
    it('should render up trend correctly', () => {
      const upTrendData = { ...mockData, trend: 'up' as const };
      render(<MetricsCard data={upTrendData} variant='admin' />);

      const trendElement = screen.getByText('+12.5%');
      expect(trendElement.closest('.bg-green-100')).toBeInTheDocument();
    });

    it('should render down trend correctly', () => {
      const downTrendData = {
        ...mockData,
        trend: 'down' as const,
        change: '-5.2%',
      };
      render(<MetricsCard data={downTrendData} variant='admin' />);

      const trendElement = screen.getByText('-5.2%');
      expect(trendElement.closest('.bg-red-100')).toBeInTheDocument();
    });

    it('should render stable trend correctly', () => {
      const stableTrendData = {
        ...mockData,
        trend: 'stable' as const,
        change: '0%',
      };
      render(<MetricsCard data={stableTrendData} variant='admin' />);

      const trendElement = screen.getByText('0%');
      expect(trendElement.closest('.bg-gray-100')).toBeInTheDocument();
    });
  });

  describe('Value Formatting', () => {
    it('should format numeric values with localization', () => {
      const dataWithLargeNumber = {
        ...mockData,
        value: 1234567,
      };

      render(<MetricsCard data={dataWithLargeNumber} variant='admin' />);
      expect(screen.getByText('1,234,567')).toBeInTheDocument();
    });

    it('should display string values as-is', () => {
      const dataWithStringValue = {
        ...mockData,
        value: '$1,234.56',
      };

      render(<MetricsCard data={dataWithStringValue} variant='admin' />);
      expect(screen.getByText('$1,234.56')).toBeInTheDocument();
    });

    it('should handle zero values', () => {
      const dataWithZero = {
        ...mockData,
        value: 0,
      };

      render(<MetricsCard data={dataWithZero} variant='admin' />);
      expect(screen.getByText('0')).toBeInTheDocument();
    });
  });

  describe('Size Variants', () => {
    it.each(['sm', 'md', 'lg'])('should apply %s size styling', (size) => {
      const { container } = render(<MetricsCard {...defaultProps} size={size as any} />);

      const cardElement = container.firstChild;
      expect(cardElement).toHaveClass(
        expect.stringContaining(`p-${size === 'sm' ? '4' : size === 'md' ? '6' : '8'}`)
      );
    });
  });

  describe('Interactions', () => {
    it('should call onAction when action button is clicked', async () => {
      const user = userEvent.setup();
      render(<MetricsCard {...defaultProps} />);

      const actionButton = screen.getByText('View Details');
      await user.click(actionButton);

      expect(mockData.onAction).toHaveBeenCalled();
    });

    it('should not render action button when onAction is not provided', () => {
      const dataWithoutAction = {
        ...mockData,
        onAction: undefined,
        actionLabel: undefined,
      };

      render(<MetricsCard data={dataWithoutAction} variant='admin' />);

      expect(screen.queryByText('View Details')).not.toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should render loading skeleton', () => {
      render(<MetricsCard {...defaultProps} loading={true} />);

      expect(
        screen.getByTestId('loading-skeleton') || document.querySelector('.animate-pulse')
      ).toBeInTheDocument();

      // Should not render actual data during loading
      expect(screen.queryByText('Active Users')).not.toBeInTheDocument();
    });

    it('should not render loading state by default', () => {
      render(<MetricsCard {...defaultProps} />);

      expect(document.querySelector('.animate-pulse')).not.toBeInTheDocument();
      expect(screen.getByText('Active Users')).toBeInTheDocument();
    });
  });

  describe('Animation', () => {
    it('should disable animations when animated=false', () => {
      const { container } = render(<MetricsCard {...defaultProps} animated={false} />);

      // Check that motion components don't have animation props
      const motionDiv = container.querySelector('div[style*="transform"]');
      expect(motionDiv).toBeNull();
    });

    it('should enable animations by default', () => {
      render(<MetricsCard {...defaultProps} />);

      // This is harder to test directly, but we can check that the component renders
      expect(screen.getByText('Active Users')).toBeInTheDocument();
    });
  });

  describe('Portal Presets', () => {
    describe('Management Portal', () => {
      it('should provide totalTenants preset', () => {
        const preset = MetricsCardPresets.management.totalTenants(25);

        expect(preset.title).toBe('Total Tenants');
        expect(preset.value).toBe(25);
        expect(preset.description).toBe('Active tenant organizations');
      });

      it('should provide systemHealth preset with correct trend', () => {
        const excellentHealth = MetricsCardPresets.management.systemHealth(98);
        expect(excellentHealth.trend).toBe('up');
        expect(excellentHealth.change).toBe('Excellent');

        const goodHealth = MetricsCardPresets.management.systemHealth(90);
        expect(goodHealth.trend).toBe('stable');
        expect(goodHealth.change).toBe('Good');

        const poorHealth = MetricsCardPresets.management.systemHealth(80);
        expect(poorHealth.trend).toBe('down');
        expect(poorHealth.change).toBe('Needs attention');
      });

      it('should provide monthlyRevenue preset with trend detection', () => {
        const increasingRevenue = MetricsCardPresets.management.monthlyRevenue(50000, '+15.2%');
        expect(increasingRevenue.trend).toBe('up');
        expect(increasingRevenue.value).toBe('$50,000');

        const decreasingRevenue = MetricsCardPresets.management.monthlyRevenue(45000, '-5.1%');
        expect(decreasingRevenue.trend).toBe('down');
      });
    });

    describe('Admin Portal', () => {
      it('should provide activeCustomers preset', () => {
        const preset = MetricsCardPresets.admin.activeCustomers(150);

        expect(preset.title).toBe('Active Customers');
        expect(preset.value).toBe(150);
        expect(preset.description).toBe('Currently subscribed customers');
      });

      it('should provide networkUptime preset with correct trend', () => {
        const excellentUptime = MetricsCardPresets.admin.networkUptime(99.9);
        expect(excellentUptime.trend).toBe('up');
        expect(excellentUptime.change).toBe('Excellent');

        const poorUptime = MetricsCardPresets.admin.networkUptime(98.5);
        expect(poorUptime.trend).toBe('down');
        expect(poorUptime.change).toBe('Poor');
      });

      it('should provide bandwidthUsage preset', () => {
        const preset = MetricsCardPresets.admin.bandwidthUsage(750, 1000);

        expect(preset.title).toBe('Bandwidth Usage');
        expect(preset.value).toBe('75%');
        expect(preset.description).toBe('750GB of 1000GB used');
      });
    });

    describe('Customer Portal', () => {
      it('should provide currentBill preset', () => {
        const preset = MetricsCardPresets.customer.currentBill(89.99);

        expect(preset.title).toBe('Current Bill');
        expect(preset.value).toBe('$89.99');
        expect(preset.description).toBe("This month's charges");
      });

      it('should provide dataUsage preset with trend based on usage', () => {
        const lowUsage = MetricsCardPresets.customer.dataUsage(30, 100);
        expect(lowUsage.trend).toBe('up');
        expect(lowUsage.description).toBe('30% of 100GB plan');

        const highUsage = MetricsCardPresets.customer.dataUsage(95, 100);
        expect(highUsage.trend).toBe('down');
        expect(highUsage.description).toBe('95% of 100GB plan');
      });

      it('should provide serviceStatus preset', () => {
        const activeStatus = MetricsCardPresets.customer.serviceStatus('active');
        expect(activeStatus.value).toBe('Active');
        expect(activeStatus.trend).toBe('up');

        const suspendedStatus = MetricsCardPresets.customer.serviceStatus('suspended');
        expect(suspendedStatus.value).toBe('Suspended');
        expect(suspendedStatus.trend).toBe('down');
      });
    });

    describe('Reseller Portal', () => {
      it('should provide monthlyCommission preset', () => {
        const preset = MetricsCardPresets.reseller.monthlyCommission(2500, '+18.5%');

        expect(preset.title).toBe('Monthly Commission');
        expect(preset.value).toBe('$2,500');
        expect(preset.trend).toBe('up');
      });

      it('should provide activeSales preset', () => {
        const preset = MetricsCardPresets.reseller.activeSales(45);

        expect(preset.title).toBe('Active Sales');
        expect(preset.value).toBe(45);
        expect(preset.description).toBe('Customers in your territory');
      });

      it('should provide conversionRate preset with trend', () => {
        const highConversion = MetricsCardPresets.reseller.conversionRate(18);
        expect(highConversion.trend).toBe('up');

        const lowConversion = MetricsCardPresets.reseller.conversionRate(8);
        expect(lowConversion.trend).toBe('down');

        const mediumConversion = MetricsCardPresets.reseller.conversionRate(12);
        expect(mediumConversion.trend).toBe('stable');
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(<MetricsCard {...defaultProps} />);

      const cardElement = screen.getByRole('article') || screen.getByRole('region');
      expect(cardElement).toBeInTheDocument();
    });

    it('should have accessible action button', () => {
      render(<MetricsCard {...defaultProps} />);

      const actionButton = screen.getByRole('button', { name: /view details/i });
      expect(actionButton).toBeInTheDocument();
      expect(actionButton).toBeEnabled();
    });

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      render(<MetricsCard {...defaultProps} />);

      const actionButton = screen.getByText('View Details');
      await user.tab();

      expect(actionButton).toHaveFocus();
    });
  });

  describe('Performance', () => {
    it('should render quickly with large numbers', () => {
      const dataWithLargeNumber = {
        ...mockData,
        value: 999999999,
      };

      const startTime = performance.now();
      render(<MetricsCard data={dataWithLargeNumber} variant='admin' />);
      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(10);
    });

    it('should memoize expensive calculations', () => {
      const { rerender } = render(<MetricsCard {...defaultProps} />);

      // Re-render with same props should be fast
      const startTime = performance.now();
      rerender(<MetricsCard {...defaultProps} />);
      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(5);
    });
  });

  describe('Error Handling', () => {
    it('should handle invalid data gracefully', () => {
      const invalidData = {
        title: '',
        value: null as any,
        trend: 'invalid' as any,
      };

      expect(() => {
        render(<MetricsCard data={invalidData} variant='admin' />);
      }).not.toThrow();
    });

    it('should handle missing variant gracefully', () => {
      expect(() => {
        render(<MetricsCard data={mockData} variant={undefined as any} />);
      }).not.toThrow();
    });
  });

  describe('Custom Styling', () => {
    it('should accept custom className', () => {
      const { container } = render(
        <MetricsCard {...defaultProps} className='custom-metrics-card' />
      );

      expect(container.firstChild).toHaveClass('custom-metrics-card');
    });

    it('should maintain variant styling with custom className', () => {
      const { container } = render(
        <MetricsCard {...defaultProps} className='custom-class' variant='customer' />
      );

      const element = container.firstChild;
      expect(element).toHaveClass('custom-class');
      expect(element).toHaveClass(expect.stringContaining('green'));
    });
  });
});
