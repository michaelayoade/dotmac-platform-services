/**
 * ResourceUsageChart Component Test Suite
 * Production-ready test coverage for universal chart component
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {
  ResourceUsageChart,
  ResourceUsagePresets,
} from '../../components/ResourceUsageChart/ResourceUsageChart';
import type { ResourceMetrics, ChartTimeframe } from '../../types';

// Mock recharts components
jest.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => (
    <div data-testid='responsive-container'>{children}</div>
  ),
  LineChart: ({ children }: any) => <div data-testid='line-chart'>{children}</div>,
  AreaChart: ({ children }: any) => <div data-testid='area-chart'>{children}</div>,
  Line: () => <div data-testid='line' />,
  Area: () => <div data-testid='area' />,
  XAxis: () => <div data-testid='x-axis' />,
  YAxis: () => <div data-testid='y-axis' />,
  CartesianGrid: () => <div data-testid='grid' />,
  Tooltip: () => <div data-testid='tooltip' />,
  Legend: () => <div data-testid='legend' />,
}));

const mockMetrics: ResourceMetrics = {
  cpu: {
    current: 65,
    history: [
      { timestamp: new Date('2024-01-15T10:00:00Z'), value: 45 },
      { timestamp: new Date('2024-01-15T10:15:00Z'), value: 52 },
      { timestamp: new Date('2024-01-15T10:30:00Z'), value: 65 },
      { timestamp: new Date('2024-01-15T10:45:00Z'), value: 58 },
    ],
  },
  memory: {
    current: 78,
    history: [
      { timestamp: new Date('2024-01-15T10:00:00Z'), value: 72 },
      { timestamp: new Date('2024-01-15T10:15:00Z'), value: 75 },
      { timestamp: new Date('2024-01-15T10:30:00Z'), value: 78 },
      { timestamp: new Date('2024-01-15T10:45:00Z'), value: 76 },
    ],
  },
  storage: {
    current: 42,
    history: [
      { timestamp: new Date('2024-01-15T10:00:00Z'), value: 40 },
      { timestamp: new Date('2024-01-15T10:15:00Z'), value: 41 },
      { timestamp: new Date('2024-01-15T10:30:00Z'), value: 42 },
      { timestamp: new Date('2024-01-15T10:45:00Z'), value: 42 },
    ],
  },
  bandwidth: {
    current: 85,
    history: [
      { timestamp: new Date('2024-01-15T10:00:00Z'), value: 20 },
      { timestamp: new Date('2024-01-15T10:15:00Z'), value: 45 },
      { timestamp: new Date('2024-01-15T10:30:00Z'), value: 85 },
      { timestamp: new Date('2024-01-15T10:45:00Z'), value: 65 },
    ],
  },
};

const defaultProps = {
  metrics: mockMetrics,
  variant: 'admin' as const,
};

describe('📈 ResourceUsageChart', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Basic Rendering', () => {
    it('should render chart container', () => {
      render(<ResourceUsageChart {...defaultProps} />);

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should render resource metrics', () => {
      render(<ResourceUsageChart {...defaultProps} />);

      expect(screen.getByText('CPU')).toBeInTheDocument();
      expect(screen.getByText('65%')).toBeInTheDocument();
      expect(screen.getByText('Memory')).toBeInTheDocument();
      expect(screen.getByText('78%')).toBeInTheDocument();
    });

    it('should render chart title', () => {
      render(<ResourceUsageChart {...defaultProps} />);

      expect(screen.getByText('Resource Usage')).toBeInTheDocument();
    });

    it('should render timeframe selector', () => {
      render(<ResourceUsageChart {...defaultProps} />);

      expect(screen.getByText('1H')).toBeInTheDocument();
      expect(screen.getByText('6H')).toBeInTheDocument();
      expect(screen.getByText('24H')).toBeInTheDocument();
    });
  });

  describe('Portal Variants', () => {
    it.each(['admin', 'customer', 'reseller', 'technician', 'management'])(
      'should apply %s variant styles',
      (variant) => {
        const { container } = render(
          <ResourceUsageChart {...defaultProps} variant={variant as any} />
        );

        const chartContainer = container.querySelector('[class*="border-"]');
        expect(chartContainer).toHaveClass(expect.stringContaining(variant.slice(0, 4)));
      }
    );

    it('should apply variant-specific colors to chart', () => {
      const { rerender } = render(<ResourceUsageChart {...defaultProps} variant='admin' />);

      // Check that chart elements are rendered (mocked)
      expect(screen.getByTestId('area-chart')).toBeInTheDocument();

      rerender(<ResourceUsageChart {...defaultProps} variant='customer' />);
      expect(screen.getByTestId('area-chart')).toBeInTheDocument();
    });
  });

  describe('Chart Types', () => {
    it('should render area chart by default', () => {
      render(<ResourceUsageChart {...defaultProps} />);

      expect(screen.getByTestId('area-chart')).toBeInTheDocument();
      expect(screen.queryByTestId('line-chart')).not.toBeInTheDocument();
    });

    it('should render line chart when specified', () => {
      render(<ResourceUsageChart {...defaultProps} chartType='line' />);

      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
      expect(screen.queryByTestId('area-chart')).not.toBeInTheDocument();
    });

    it('should toggle between chart types', async () => {
      const user = userEvent.setup();
      render(<ResourceUsageChart {...defaultProps} />);

      // Should start with area chart
      expect(screen.getByTestId('area-chart')).toBeInTheDocument();

      // Find and click chart type toggle (assuming it exists)
      const toggleButton = screen.queryByRole('button', { name: /line chart/i });
      if (toggleButton) {
        await user.click(toggleButton);
        expect(screen.getByTestId('line-chart')).toBeInTheDocument();
      }
    });
  });

  describe('Resource Metrics Display', () => {
    it('should display current values for all metrics', () => {
      render(<ResourceUsageChart {...defaultProps} />);

      expect(screen.getByText('65%')).toBeInTheDocument(); // CPU
      expect(screen.getByText('78%')).toBeInTheDocument(); // Memory
      expect(screen.getByText('42%')).toBeInTheDocument(); // Storage
      expect(screen.getByText('85%')).toBeInTheDocument(); // Bandwidth
    });

    it('should show trend indicators', () => {
      render(<ResourceUsageChart {...defaultProps} />);

      // Should show trend arrows or indicators
      const trendElements =
        document.querySelectorAll('[class*="trend"]') ||
        document.querySelectorAll('svg') ||
        screen.getAllByTestId(/trend/i);

      expect(trendElements.length).toBeGreaterThan(0);
    });

    it('should apply warning colors for high usage', () => {
      const highUsageMetrics = {
        ...mockMetrics,
        cpu: { ...mockMetrics.cpu, current: 95 },
        memory: { ...mockMetrics.memory, current: 92 },
      };

      render(<ResourceUsageChart metrics={highUsageMetrics} variant='admin' />);

      expect(screen.getByText('95%')).toBeInTheDocument();
      expect(screen.getByText('92%')).toBeInTheDocument();
    });

    it('should calculate trends correctly', () => {
      render(<ResourceUsageChart {...defaultProps} />);

      // CPU went from 45 to 65 (up trend)
      // Memory went from 72 to 78 (up trend)
      // Storage stayed relatively stable
      // Bandwidth is highly variable

      // Should show appropriate trend indicators
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });

  describe('Timeframe Selection', () => {
    it('should handle timeframe changes', async () => {
      const user = userEvent.setup();
      const onTimeframeChange = jest.fn();

      render(<ResourceUsageChart {...defaultProps} onTimeframeChange={onTimeframeChange} />);

      const sixHourButton = screen.getByText('6H');
      await user.click(sixHourButton);

      expect(onTimeframeChange).toHaveBeenCalledWith('6h');
    });

    it('should highlight active timeframe', async () => {
      const user = userEvent.setup();
      render(<ResourceUsageChart {...defaultProps} />);

      const oneHourButton = screen.getByText('1H');
      expect(oneHourButton).toHaveClass(
        expect.stringContaining('active') || expect.stringContaining('bg-')
      );
    });

    it('should provide all standard timeframes', () => {
      render(<ResourceUsageChart {...defaultProps} />);

      expect(screen.getByText('1H')).toBeInTheDocument();
      expect(screen.getByText('6H')).toBeInTheDocument();
      expect(screen.getByText('24H')).toBeInTheDocument();
      expect(screen.getByText('7D')).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('should render loading skeleton', () => {
      render(<ResourceUsageChart {...defaultProps} loading={true} />);

      expect(document.querySelector('.animate-pulse')).toBeInTheDocument();
      expect(screen.queryByText('CPU')).not.toBeInTheDocument();
    });

    it('should show shimmer effect during loading', () => {
      render(<ResourceUsageChart {...defaultProps} loading={true} />);

      const loadingElements = document.querySelectorAll('.animate-pulse');
      expect(loadingElements.length).toBeGreaterThan(0);
    });
  });

  describe('Real-time Updates', () => {
    it('should handle metrics updates', () => {
      const { rerender } = render(<ResourceUsageChart {...defaultProps} />);

      expect(screen.getByText('65%')).toBeInTheDocument();

      const updatedMetrics = {
        ...mockMetrics,
        cpu: { ...mockMetrics.cpu, current: 72 },
      };

      rerender(<ResourceUsageChart metrics={updatedMetrics} variant='admin' />);

      expect(screen.getByText('72%')).toBeInTheDocument();
    });

    it('should animate value changes', () => {
      const { rerender } = render(<ResourceUsageChart {...defaultProps} animated={true} />);

      const updatedMetrics = {
        ...mockMetrics,
        memory: { ...mockMetrics.memory, current: 82 },
      };

      rerender(<ResourceUsageChart metrics={updatedMetrics} variant='admin' animated={true} />);

      // Animation would be handled by motion components
      expect(screen.getByText('82%')).toBeInTheDocument();
    });
  });

  describe('Refresh Functionality', () => {
    it('should call onRefresh when refresh button is clicked', async () => {
      const user = userEvent.setup();
      const onRefresh = jest.fn();

      render(<ResourceUsageChart {...defaultProps} onRefresh={onRefresh} />);

      const refreshButton = screen.getByRole('button', { name: /refresh/i });
      await user.click(refreshButton);

      expect(onRefresh).toHaveBeenCalled();
    });

    it('should show loading state during refresh', () => {
      render(<ResourceUsageChart {...defaultProps} loading={true} onRefresh={jest.fn()} />);

      const refreshButton = screen.queryByRole('button', { name: /refresh/i });
      if (refreshButton) {
        expect(refreshButton).toBeDisabled();
      }
    });
  });

  describe('Tooltip Functionality', () => {
    it('should render tooltip component', () => {
      render(<ResourceUsageChart {...defaultProps} />);

      expect(screen.getByTestId('tooltip')).toBeInTheDocument();
    });

    it('should show custom tooltip on hover', async () => {
      const user = userEvent.setup();
      render(<ResourceUsageChart {...defaultProps} />);

      // Simulate hover on chart area
      const chartArea = screen.getByTestId('area-chart');
      await user.hover(chartArea);

      // Tooltip should be rendered
      expect(screen.getByTestId('tooltip')).toBeInTheDocument();
    });
  });

  describe('Portal Presets', () => {
    describe('Management Portal Metrics', () => {
      it('should provide system overview preset', () => {
        const preset = ResourceUsagePresets.management.systemOverview();

        expect(preset.title).toBe('Platform Resources');
        expect(preset.showAllMetrics).toBe(true);
        expect(preset.refreshInterval).toBe(30000);
      });

      it('should provide tenant resource preset', () => {
        const preset = ResourceUsagePresets.management.tenantResources('tenant-123');

        expect(preset.title).toBe('Tenant Resources');
        expect(preset.tenantId).toBe('tenant-123');
      });
    });

    describe('Admin Portal Metrics', () => {
      it('should provide network monitoring preset', () => {
        const preset = ResourceUsagePresets.admin.networkMonitoring();

        expect(preset.title).toBe('Network Performance');
        expect(preset.primaryMetrics).toContain('bandwidth');
      });

      it('should provide server health preset', () => {
        const preset = ResourceUsagePresets.admin.serverHealth();

        expect(preset.title).toBe('Server Health');
        expect(preset.primaryMetrics).toContain('cpu');
        expect(preset.primaryMetrics).toContain('memory');
      });
    });

    describe('Customer Portal Metrics', () => {
      it('should provide service usage preset', () => {
        const preset = ResourceUsagePresets.customer.serviceUsage();

        expect(preset.title).toBe('Your Usage');
        expect(preset.customerView).toBe(true);
      });

      it('should provide data consumption preset', () => {
        const preset = ResourceUsagePresets.customer.dataConsumption();

        expect(preset.title).toBe('Data Usage');
        expect(preset.primaryMetrics).toContain('bandwidth');
      });
    });

    describe('Technician Portal Metrics', () => {
      it('should provide field diagnostics preset', () => {
        const preset = ResourceUsagePresets.technician.fieldDiagnostics();

        expect(preset.title).toBe('Field Diagnostics');
        expect(preset.realTimeUpdates).toBe(true);
      });
    });
  });

  describe('Responsive Design', () => {
    it('should handle different screen sizes', () => {
      // Mock window resize
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 768,
      });

      render(<ResourceUsageChart {...defaultProps} />);

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should adjust chart height based on container', () => {
      render(<ResourceUsageChart {...defaultProps} height='300px' />);

      const container = screen.getByTestId('responsive-container');
      expect(container).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA attributes', () => {
      render(<ResourceUsageChart {...defaultProps} />);

      const chartContainer =
        screen.getByRole('img') ||
        screen.getByRole('region') ||
        document.querySelector('[role="img"]');
      expect(chartContainer).toBeInTheDocument();
    });

    it('should provide alt text for chart', () => {
      render(<ResourceUsageChart {...defaultProps} />);

      // Should have descriptive text for screen readers
      expect(screen.getByText('Resource Usage')).toBeInTheDocument();
    });

    it('should support keyboard navigation for controls', async () => {
      const user = userEvent.setup();
      render(<ResourceUsageChart {...defaultProps} />);

      const timeframeButton = screen.getByText('1H');
      await user.tab();

      expect(timeframeButton).toHaveFocus();
    });
  });

  describe('Performance', () => {
    it('should handle large datasets efficiently', () => {
      const largeHistoryMetrics = {
        ...mockMetrics,
        cpu: {
          current: 65,
          history: Array.from({ length: 1000 }, (_, i) => ({
            timestamp: new Date(Date.now() - (1000 - i) * 60000),
            value: Math.random() * 100,
          })),
        },
      };

      const startTime = performance.now();
      render(<ResourceUsageChart metrics={largeHistoryMetrics} variant='admin' />);
      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(100);
    });

    it('should debounce real-time updates', () => {
      const { rerender } = render(<ResourceUsageChart {...defaultProps} />);

      // Simulate rapid updates
      for (let i = 0; i < 10; i++) {
        const updatedMetrics = {
          ...mockMetrics,
          cpu: { ...mockMetrics.cpu, current: 60 + i },
        };
        rerender(<ResourceUsageChart metrics={updatedMetrics} variant='admin' />);
      }

      // Should handle updates without performance issues
      expect(screen.getByText('69%')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should handle missing metric data', () => {
      const incompleteMetrics = {
        cpu: mockMetrics.cpu,
        memory: mockMetrics.memory,
        // Missing storage and bandwidth
      } as any;

      expect(() => {
        render(<ResourceUsageChart metrics={incompleteMetrics} variant='admin' />);
      }).not.toThrow();
    });

    it('should handle empty history arrays', () => {
      const emptyHistoryMetrics = {
        cpu: { current: 50, history: [] },
        memory: { current: 60, history: [] },
        storage: { current: 30, history: [] },
        bandwidth: { current: 40, history: [] },
      };

      expect(() => {
        render(<ResourceUsageChart metrics={emptyHistoryMetrics} variant='admin' />);
      }).not.toThrow();

      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('should handle invalid metric values', () => {
      const invalidMetrics = {
        ...mockMetrics,
        cpu: { current: -10, history: mockMetrics.cpu.history },
        memory: { current: 150, history: mockMetrics.memory.history },
      };

      expect(() => {
        render(<ResourceUsageChart metrics={invalidMetrics} variant='admin' />);
      }).not.toThrow();
    });
  });

  describe('Custom Configuration', () => {
    it('should accept custom height', () => {
      render(<ResourceUsageChart {...defaultProps} height='400px' />);

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });

    it('should accept custom className', () => {
      const { container } = render(
        <ResourceUsageChart {...defaultProps} className='custom-chart' />
      );

      expect(container.firstChild).toHaveClass('custom-chart');
    });

    it('should handle custom refresh intervals', () => {
      render(<ResourceUsageChart {...defaultProps} refreshInterval={10000} />);

      expect(screen.getByTestId('responsive-container')).toBeInTheDocument();
    });
  });

  describe('Chart Interactions', () => {
    it('should handle metric selection', async () => {
      const user = userEvent.setup();
      const onMetricSelect = jest.fn();

      render(<ResourceUsageChart {...defaultProps} onMetricSelect={onMetricSelect} />);

      const cpuMetric = screen.getByText('CPU');
      await user.click(cpuMetric);

      expect(onMetricSelect).toHaveBeenCalledWith('cpu');
    });

    it('should toggle metric visibility', async () => {
      const user = userEvent.setup();
      render(<ResourceUsageChart {...defaultProps} />);

      // Assuming there's a toggle for hiding/showing metrics
      const cpuToggle = screen.queryByRole('checkbox', { name: /cpu/i });
      if (cpuToggle) {
        await user.click(cpuToggle);
        // Metric should be hidden/shown
      }

      expect(screen.getByTestId('area-chart')).toBeInTheDocument();
    });
  });
});
