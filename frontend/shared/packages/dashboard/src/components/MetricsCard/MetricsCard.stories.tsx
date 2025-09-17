import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import { MetricsCard, MetricsCardPresets, METRICS_TEMPLATES } from './MetricsCard';
import {
  Users,
  DollarSign,
  Activity,
  TrendingUp,
  Server,
  Globe,
  Wifi,
  HardDrive,
  Clock
} from 'lucide-react';
import type { MetricsCardData } from '../../types';

const meta: Meta<typeof MetricsCard> = {
  title: 'Dashboard/MetricsCard',
  component: MetricsCard,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
Universal MetricsCard component with portal-specific variants and comprehensive functionality.

## Features
- Portal-specific styling and branding
- Trend indicators (up, down, stable)
- Animated value display
- Loading states with skeleton
- Action buttons for interactions
- Icon support with portal-specific colors
- Responsive design

## Usage
\`\`\`tsx
import { MetricsCard, MetricsCardPresets } from '@dotmac/dashboard';

// Using presets
<MetricsCard
  variant="admin"
  data={MetricsCardPresets.admin.activeCustomers(1247)}
/>

// Custom data
<MetricsCard
  variant="customer"
  data={{
    title: 'Data Usage',
    value: '45.2 GB',
    trend: 'up',
    change: '+5% this month',
    description: 'Current billing cycle',
    icon: Activity
  }}
/>
\`\`\`
      `,
    },
    a11y: {
      config: {
        rules: [
          { id: 'color-contrast', enabled: true },
          { id: 'button-name', enabled: true },
        ],
      },
    },
  },
  tags: ['autodocs', 'dashboard', 'metrics'],
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['admin', 'customer', 'reseller', 'technician', 'management'],
      description: 'Portal variant for styling and branding',
    },
    size: {
      control: { type: 'select' },
      options: ['sm', 'md', 'lg'],
      description: 'Card size',
    },
    loading: {
      control: 'boolean',
      description: 'Loading state with skeleton animation',
    },
    animated: {
      control: 'boolean',
      description: 'Enable entrance animations',
    },
  },
} satisfies Meta<typeof MetricsCard>;

export default meta;
type Story = StoryObj<typeof meta>;

// Sample data for stories
const sampleMetrics = {
  users: {
    title: 'Active Users',
    value: 1247,
    change: '+12%',
    trend: 'up' as const,
    description: 'Currently online',
    icon: Users,
  },
  revenue: {
    title: 'Monthly Revenue',
    value: '$45,280',
    change: '+8.2%',
    trend: 'up' as const,
    description: 'vs last month',
    icon: DollarSign,
  },
  uptime: {
    title: 'System Uptime',
    value: '99.97%',
    change: 'Stable',
    trend: 'stable' as const,
    description: 'Last 30 days',
    icon: Activity,
  },
  dataUsage: {
    title: 'Data Usage',
    value: '45.2 GB',
    change: '+15%',
    trend: 'up' as const,
    description: 'This billing cycle',
    icon: Globe,
  },
  commission: {
    title: 'Total Commission',
    value: '$3,247.50',
    change: '+5.3%',
    trend: 'up' as const,
    description: 'This month',
    icon: TrendingUp,
  },
  jobs: {
    title: 'Completed Jobs',
    value: 28,
    change: '+4',
    trend: 'up' as const,
    description: 'This week',
    icon: Clock,
  },
  servers: {
    title: 'Active Servers',
    value: 156,
    change: 'Stable',
    trend: 'stable' as const,
    description: 'All regions',
    icon: Server,
  }
} satisfies Record<string, MetricsCardData>;

// Basic usage
export const Default: Story = {
  args: {
    variant: 'admin',
    data: sampleMetrics.users,
  },
};

// Portal variants
export const AdminPortal: Story = {
  args: {
    variant: 'admin',
    data: sampleMetrics.users,
  },
  parameters: {
    portal: 'admin',
    docs: {
      description: {
        story: 'Admin portal metrics card with blue branding.',
      },
    },
  },
};

export const CustomerPortal: Story = {
  args: {
    variant: 'customer',
    data: sampleMetrics.dataUsage,
  },
  parameters: {
    portal: 'customer',
    docs: {
      description: {
        story: 'Customer portal metrics card with green branding.',
      },
    },
  },
};

export const ResellerPortal: Story = {
  args: {
    variant: 'reseller',
    data: sampleMetrics.commission,
  },
  parameters: {
    portal: 'reseller',
    docs: {
      description: {
        story: 'Reseller portal metrics card with purple branding.',
      },
    },
  },
};

export const TechnicianPortal: Story = {
  args: {
    variant: 'technician',
    data: sampleMetrics.jobs,
  },
  parameters: {
    portal: 'technician',
    docs: {
      description: {
        story: 'Technician portal metrics card with orange branding.',
      },
    },
  },
};

export const ManagementPortal: Story = {
  args: {
    variant: 'management',
    data: sampleMetrics.servers,
  },
  parameters: {
    portal: 'management',
    docs: {
      description: {
        story: 'Management portal metrics card with indigo branding.',
      },
    },
  },
};

// Size variants
export const SmallSize: Story = {
  args: {
    variant: 'admin',
    size: 'sm',
    data: sampleMetrics.users,
  },
};

export const MediumSize: Story = {
  args: {
    variant: 'admin',
    size: 'md',
    data: sampleMetrics.users,
  },
};

export const LargeSize: Story = {
  args: {
    variant: 'admin',
    size: 'lg',
    data: sampleMetrics.users,
  },
};

// Trend variants
export const PositiveTrend: Story = {
  args: {
    variant: 'admin',
    data: sampleMetrics.revenue,
  },
  parameters: {
    docs: {
      description: {
        story: 'Metrics card showing positive trend with green indicator.',
      },
    },
  },
};

export const NegativeTrend: Story = {
  args: {
    variant: 'admin',
    data: {
      ...sampleMetrics.users,
      trend: 'down',
      change: '-5.2%',
      value: 1189,
    },
  },
  parameters: {
    docs: {
      description: {
        story: 'Metrics card showing negative trend with red indicator.',
      },
    },
  },
};

export const StableTrend: Story = {
  args: {
    variant: 'admin',
    data: sampleMetrics.uptime,
  },
  parameters: {
    docs: {
      description: {
        story: 'Metrics card showing stable trend with gray indicator.',
      },
    },
  },
};

// Loading state
export const Loading: Story = {
  args: {
    variant: 'admin',
    loading: true,
    data: sampleMetrics.users,
  },
  parameters: {
    docs: {
      description: {
        story: 'Loading state with skeleton animation.',
      },
    },
  },
};

// With action button
export const WithAction: Story = {
  args: {
    variant: 'admin',
    data: {
      ...sampleMetrics.users,
      actionLabel: 'View Details',
      onAction: fn(),
    },
  },
  parameters: {
    docs: {
      description: {
        story: 'Metrics card with action button for additional functionality.',
      },
    },
  },
};

// Without icon
export const WithoutIcon: Story = {
  args: {
    variant: 'admin',
    data: {
      title: 'Simple Metric',
      value: 42,
      change: '+10%',
      trend: 'up' as const,
      description: 'No icon variant',
    },
  },
};

// Long values
export const LongValues: Story = {
  args: {
    variant: 'admin',
    data: {
      title: 'Very Long Metric Title That May Wrap',
      value: '$1,234,567,890',
      change: '+123.45%',
      trend: 'up' as const,
      description: 'This is a very long description that demonstrates how the card handles longer text content gracefully',
      icon: DollarSign,
    },
  },
};

// Real-time demo
export const RealTimeDemo: Story = {
  render: (args) => {
    const [value, setValue] = React.useState(1247);
    const [trend, setTrend] = React.useState<'up' | 'down' | 'stable'>('up');

    React.useEffect(() => {
      const interval = setInterval(() => {
        const change = Math.floor(Math.random() * 20) - 10; // -10 to +10
        const newValue = Math.max(1000, value + change);
        setValue(newValue);
        setTrend(change > 5 ? 'up' : change < -5 ? 'down' : 'stable');
      }, 2000);

      return () => clearInterval(interval);
    }, [value]);

    return (
      <MetricsCard
        {...args}
        variant="admin"
        data={{
          title: 'Active Users (Live)',
          value: value,
          change: `${trend === 'up' ? '+' : trend === 'down' ? '-' : '±'}${Math.abs(Math.floor(Math.random() * 10))}%`,
          trend,
          description: 'Updates every 2 seconds',
          icon: Users,
        }}
      />
    );
  },
  parameters: {
    docs: {
      description: {
        story: 'Real-time updating metrics card demonstration.',
      },
    },
  },
};

// Using presets
export const UsingPresets: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <MetricsCard
        variant="admin"
        data={MetricsCardPresets.admin.activeCustomers(1247)}
      />
      <MetricsCard
        variant="admin"
        data={MetricsCardPresets.admin.networkUptime(99.97)}
      />
      <MetricsCard
        variant="admin"
        data={MetricsCardPresets.admin.monthlyRevenue(45280, '+8.2%')}
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Using built-in presets for common metrics.',
      },
    },
  },
};

// Portal showcase
export const AllPortalVariants: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
      <MetricsCard
        variant="admin"
        data={sampleMetrics.users}
      />
      <MetricsCard
        variant="customer"
        data={sampleMetrics.dataUsage}
      />
      <MetricsCard
        variant="reseller"
        data={sampleMetrics.commission}
      />
      <MetricsCard
        variant="technician"
        data={sampleMetrics.jobs}
      />
      <MetricsCard
        variant="management"
        data={sampleMetrics.servers}
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'All portal variants showing consistent branding and styling.',
      },
    },
  },
};

// Different metric types
export const MetricTypes: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricsCard
        variant="admin"
        data={{
          title: 'Percentage',
          value: '99.97%',
          trend: 'stable',
          change: 'Excellent',
          description: 'System uptime',
          icon: Activity,
        }}
      />
      <MetricsCard
        variant="customer"
        data={{
          title: 'Currency',
          value: '$45,280',
          trend: 'up',
          change: '+8.2%',
          description: 'Monthly billing',
          icon: DollarSign,
        }}
      />
      <MetricsCard
        variant="reseller"
        data={{
          title: 'Count',
          value: 1247,
          trend: 'up',
          change: '+45 today',
          description: 'Total customers',
          icon: Users,
        }}
      />
      <MetricsCard
        variant="technician"
        data={{
          title: 'Data Size',
          value: '2.4 TB',
          trend: 'up',
          change: '+120 GB',
          description: 'Storage used',
          icon: HardDrive,
        }}
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Different types of metrics: percentages, currency, counts, and data sizes.',
      },
    },
  },
};

// Size showcase
export const AllSizes: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <MetricsCard
        variant="admin"
        size="sm"
        data={{ ...sampleMetrics.users, title: 'Small Card' }}
      />
      <MetricsCard
        variant="admin"
        size="md"
        data={{ ...sampleMetrics.users, title: 'Medium Card' }}
      />
      <MetricsCard
        variant="admin"
        size="lg"
        data={{ ...sampleMetrics.users, title: 'Large Card' }}
      />
    </div>
  ),
};

// Interactive dashboard demo
export const InteractiveDashboard: Story = {
  render: () => {
    const [selectedMetric, setSelectedMetric] = React.useState<string | null>(null);

    const metrics = [
      { key: 'users', ...sampleMetrics.users, variant: 'admin' as const },
      { key: 'revenue', ...sampleMetrics.revenue, variant: 'customer' as const },
      { key: 'uptime', ...sampleMetrics.uptime, variant: 'reseller' as const },
      { key: 'jobs', ...sampleMetrics.jobs, variant: 'technician' as const },
    ];

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {metrics.map((metric) => (
            <div
              key={metric.key}
              className={`cursor-pointer transition-transform hover:scale-105 ${
                selectedMetric === metric.key ? 'ring-2 ring-blue-500 ring-offset-2 rounded-lg' : ''
              }`}
              onClick={() => setSelectedMetric(selectedMetric === metric.key ? null : metric.key)}
            >
              <MetricsCard
                variant={metric.variant}
                data={{
                  ...metric,
                  actionLabel: selectedMetric === metric.key ? 'Selected' : 'View',
                  onAction: () => setSelectedMetric(metric.key),
                }}
              />
            </div>
          ))}
        </div>

        {selectedMetric && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h4 className="font-medium text-blue-900">Selected Metric: {selectedMetric}</h4>
            <p className="text-sm text-blue-700 mt-1">
              Click on a different card to select it, or click the same card again to deselect.
            </p>
          </div>
        )}
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story: 'Interactive dashboard with selectable metrics cards.',
      },
    },
  },
};

// Templates demonstration
export const TemplatesDemo: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricsCard
        variant="management"
        data={METRICS_TEMPLATES.health(98.5)}
      />
      <MetricsCard
        variant="admin"
        data={METRICS_TEMPLATES.uptime(99.97)}
      />
      <MetricsCard
        variant="customer"
        data={METRICS_TEMPLATES.customers(1247)}
      />
      <MetricsCard
        variant="reseller"
        data={METRICS_TEMPLATES.revenue(45280, '+8.2%')}
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Using built-in metric templates for consistent data display.',
      },
    },
  },
};
