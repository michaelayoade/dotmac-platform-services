import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import { ActivityFeed, ActivityFeedPresets, ACTIVITY_TEMPLATES } from './ActivityFeed';
import type { Activity } from '../../types';

const meta: Meta<typeof ActivityFeed> = {
  title: 'Dashboard/ActivityFeed',
  component: ActivityFeed,
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        component: `
Universal ActivityFeed component with portal-specific variants and comprehensive functionality.

## Features
- Portal-specific styling and branding
- Activity type filtering (info, success, warning, error)
- Search functionality across titles, descriptions, and usernames
- Real-time refresh capability
- Expandable list with pagination
- Loading states with skeleton animation
- Click handling for activity items
- User avatars and metadata display

## Usage
\`\`\`tsx
import { ActivityFeed, ACTIVITY_TEMPLATES } from '@dotmac/dashboard';

const activities = [
  ACTIVITY_TEMPLATES.customerSignup('user@example.com', 'Premium'),
  ACTIVITY_TEMPLATES.systemAlert('Server load is high', 'warning'),
];

<ActivityFeed
  variant="admin"
  activities={activities}
  onActivityClick={handleActivityClick}
  onRefresh={handleRefresh}
/>
\`\`\`
      `,
    },
    a11y: {
      config: {
        rules: [
          { id: 'color-contrast', enabled: true },
          { id: 'button-name', enabled: true },
          { id: 'list', enabled: true },
        ],
      },
    },
  },
  tags: ['autodocs', 'dashboard', 'activity'],
  argTypes: {
    variant: {
      control: { type: 'select' },
      options: ['admin', 'customer', 'reseller', 'technician', 'management'],
      description: 'Portal variant for styling and branding',
    },
    loading: {
      control: 'boolean',
      description: 'Loading state with skeleton animation',
    },
    config: {
      control: 'object',
      description: 'Configuration options for the activity feed',
    },
  },
  args: {
    onActivityClick: fn(),
    onRefresh: fn(),
  },
} satisfies Meta<typeof ActivityFeed>;

export default meta;
type Story = StoryObj<typeof meta>;

// Sample activities for stories
const generateSampleActivities = (): Activity[] => [
  {
    id: '1',
    type: 'success',
    title: 'New Customer Signup',
    description: 'john.doe@example.com signed up for Premium plan',
    timestamp: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
    userName: 'System',
    metadata: { plan: 'Premium', email: 'john.doe@example.com' }
  },
  {
    id: '2',
    type: 'info',
    title: 'Payment Processed',
    description: 'Monthly payment of $99.99 received from customer #1247',
    timestamp: new Date(Date.now() - 15 * 60 * 1000), // 15 minutes ago
    userName: 'Payment Gateway',
    metadata: { amount: 99.99, customerId: '1247' }
  },
  {
    id: '3',
    type: 'warning',
    title: 'High Network Load',
    description: 'Network utilization reached 85% in US-West region',
    timestamp: new Date(Date.now() - 45 * 60 * 1000), // 45 minutes ago
    userName: 'Network Monitor',
    metadata: { region: 'US-West', utilization: 85 }
  },
  {
    id: '4',
    type: 'error',
    title: 'Service Outage',
    description: 'DNS resolution issues affecting customers in Europe region',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
    userName: 'NOC Team',
    metadata: { region: 'Europe', service: 'DNS', status: 'investigating' }
  },
  {
    id: '5',
    type: 'success',
    title: 'System Update Completed',
    description: 'Security patches applied successfully across all servers',
    timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000), // 3 hours ago
    userName: 'DevOps Team',
    metadata: { updateType: 'security', serversAffected: 156 }
  },
  {
    id: '6',
    type: 'info',
    title: 'Backup Completed',
    description: 'Daily database backup completed successfully (2.4GB)',
    timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000), // 6 hours ago
    userName: 'Backup Service',
    metadata: { size: '2.4GB', type: 'database' }
  },
  {
    id: '7',
    type: 'success',
    title: 'New Feature Released',
    description: 'Advanced analytics dashboard is now available to all users',
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1 day ago
    userName: 'Product Team',
    metadata: { feature: 'analytics', version: '2.1.0' }
  },
  {
    id: '8',
    type: 'info',
    title: 'Maintenance Scheduled',
    description: 'Routine maintenance scheduled for next Sunday 2:00 AM UTC',
    timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // 2 days ago
    userName: 'Operations Team',
    metadata: { scheduledDate: '2024-03-17', duration: '2 hours' }
  }
];

// Basic usage
export const Default: Story = {
  args: {
    variant: 'admin',
    activities: generateSampleActivities(),
  },
};

// Portal variants
export const AdminPortal: Story = {
  args: {
    variant: 'admin',
    activities: generateSampleActivities(),
  },
  parameters: {
    portal: 'admin',
    docs: {
      description: {
        story: 'Admin portal activity feed with blue branding.',
      },
    },
  },
};

export const CustomerPortal: Story = {
  args: {
    variant: 'customer',
    activities: [
      {
        id: '1',
        type: 'info',
        title: 'Bill Generated',
        description: 'Your monthly bill of $49.99 is ready for review',
        timestamp: new Date(Date.now() - 10 * 60 * 1000),
        metadata: { amount: 49.99, dueDate: '2024-03-15' }
      },
      {
        id: '2',
        type: 'success',
        title: 'Payment Confirmed',
        description: 'Your payment has been processed successfully',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
        metadata: { amount: 49.99, method: 'Credit Card' }
      },
      {
        id: '3',
        type: 'warning',
        title: 'Data Usage Alert',
        description: 'You have used 80% of your monthly data allowance',
        timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000),
        metadata: { usage: '80GB', limit: '100GB' }
      },
    ],
  },
  parameters: {
    portal: 'customer',
    docs: {
      description: {
        story: 'Customer portal activity feed with green branding.',
      },
    },
  },
};

export const ResellerPortal: Story = {
  args: {
    variant: 'reseller',
    activities: [
      {
        id: '1',
        type: 'success',
        title: 'Commission Earned',
        description: 'Commission of $150.00 earned from customer referral',
        timestamp: new Date(Date.now() - 30 * 60 * 1000),
        metadata: { amount: 150.00, customerId: 'CUST-456' }
      },
      {
        id: '2',
        type: 'info',
        title: 'New Lead Assigned',
        description: 'Enterprise lead from TechCorp has been assigned to you',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
        metadata: { company: 'TechCorp', value: 5000, priority: 'high' }
      },
      {
        id: '3',
        type: 'success',
        title: 'Customer Upgraded',
        description: 'Customer upgraded from Basic to Premium plan',
        timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
        metadata: { fromPlan: 'Basic', toPlan: 'Premium', customerId: 'CUST-789' }
      },
    ],
  },
  parameters: {
    portal: 'reseller',
    docs: {
      description: {
        story: 'Reseller portal activity feed with purple branding.',
      },
    },
  },
};

export const TechnicianPortal: Story = {
  args: {
    variant: 'technician',
    activities: [
      {
        id: '1',
        type: 'info',
        title: 'Job Assigned',
        description: 'Installation job at 123 Main St scheduled for 2:00 PM',
        timestamp: new Date(Date.now() - 15 * 60 * 1000),
        userName: 'Dispatch',
        metadata: { address: '123 Main St', time: '14:00', type: 'installation' }
      },
      {
        id: '2',
        type: 'success',
        title: 'Job Completed',
        description: 'Maintenance work at Tech Park completed successfully',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
        userName: 'Tech-001',
        metadata: { location: 'Tech Park', duration: '1.5 hours', type: 'maintenance' }
      },
      {
        id: '3',
        type: 'warning',
        title: 'Equipment Alert',
        description: 'Router at site B requires immediate attention',
        timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
        userName: 'Monitoring System',
        metadata: { site: 'Site B', equipment: 'Router', severity: 'medium' }
      },
    ],
  },
  parameters: {
    portal: 'technician',
    docs: {
      description: {
        story: 'Technician portal activity feed with orange branding.',
      },
    },
  },
};

export const ManagementPortal: Story = {
  args: {
    variant: 'management',
    activities: [
      {
        id: '1',
        type: 'success',
        title: 'Monthly Target Achieved',
        description: 'Revenue target of $250K exceeded with $287K total',
        timestamp: new Date(Date.now() - 60 * 60 * 1000),
        userName: 'Analytics Engine',
        metadata: { target: 250000, actual: 287000, variance: '+14.8%' }
      },
      {
        id: '2',
        type: 'info',
        title: 'New Tenant Onboarded',
        description: 'Enterprise client "Global Corp" successfully onboarded',
        timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000),
        userName: 'Onboarding Team',
        metadata: { client: 'Global Corp', tier: 'Enterprise', value: 50000 }
      },
      {
        id: '3',
        type: 'warning',
        title: 'SLA Risk Alert',
        description: 'Customer satisfaction score dropped to 4.1/5.0',
        timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000),
        userName: 'Quality Assurance',
        metadata: { score: 4.1, previous: 4.5, threshold: 4.0 }
      },
    ],
  },
  parameters: {
    portal: 'management',
    docs: {
      description: {
        story: 'Management portal activity feed with indigo branding.',
      },
    },
  },
};

// Loading state
export const Loading: Story = {
  args: {
    variant: 'admin',
    activities: [],
    loading: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'Loading state with skeleton animation.',
      },
    },
  },
};

// Empty state
export const EmptyState: Story = {
  args: {
    variant: 'admin',
    activities: [],
  },
  parameters: {
    docs: {
      description: {
        story: 'Empty state when no activities are available.',
      },
    },
  },
};

// With configuration
export const WithConfiguration: Story = {
  args: {
    variant: 'admin',
    activities: generateSampleActivities(),
    config: {
      showFilters: false,
      showUserAvatars: false,
      maxItems: 5,
    },
  },
  parameters: {
    docs: {
      description: {
        story: 'Activity feed with custom configuration: no filters, no avatars, limited to 5 items.',
      },
    },
  },
};

// Activity types showcase
export const ActivityTypes: Story = {
  args: {
    variant: 'admin',
    activities: [
      {
        id: '1',
        type: 'info',
        title: 'Information Activity',
        description: 'This is an informational activity with details',
        timestamp: new Date(Date.now() - 5 * 60 * 1000),
        userName: 'System',
      },
      {
        id: '2',
        type: 'success',
        title: 'Success Activity',
        description: 'This activity represents a successful operation',
        timestamp: new Date(Date.now() - 10 * 60 * 1000),
        userName: 'User',
      },
      {
        id: '3',
        type: 'warning',
        title: 'Warning Activity',
        description: 'This activity shows a warning that needs attention',
        timestamp: new Date(Date.now() - 15 * 60 * 1000),
        userName: 'Monitor',
      },
      {
        id: '4',
        type: 'error',
        title: 'Error Activity',
        description: 'This activity represents an error condition',
        timestamp: new Date(Date.now() - 20 * 60 * 1000),
        userName: 'System',
      },
    ],
  },
  parameters: {
    docs: {
      description: {
        story: 'All activity types: info, success, warning, and error.',
      },
    },
  },
};

// Interactive demo
export const InteractiveDemo: Story = {
  render: (args) => {
    const [activities, setActivities] = React.useState(generateSampleActivities());
    const [loading, setLoading] = React.useState(false);

    const handleRefresh = () => {
      setLoading(true);
      setTimeout(() => {
        // Simulate adding a new activity
        const newActivity: Activity = {
          id: Date.now().toString(),
          type: 'success',
          title: 'Refresh Completed',
          description: 'Activity feed has been refreshed with latest data',
          timestamp: new Date(),
          userName: 'System',
          metadata: { action: 'refresh' }
        };
        setActivities([newActivity, ...activities]);
        setLoading(false);
      }, 1000);
    };

    const handleActivityClick = (activity: Activity) => {
      alert(`Clicked activity: ${activity.title}\n\n${activity.description}`);
    };

    return (
      <ActivityFeed
        {...args}
        activities={activities}
        loading={loading}
        onRefresh={handleRefresh}
        onActivityClick={handleActivityClick}
      />
    );
  },
  args: {
    variant: 'admin',
  },
  parameters: {
    docs: {
      description: {
        story: 'Interactive demo with refresh functionality and click handling.',
      },
    },
  },
};

// Using templates
export const UsingTemplates: Story = {
  args: {
    variant: 'admin',
    activities: [
      ACTIVITY_TEMPLATES.customerSignup('alice@company.com', 'Enterprise'),
      ACTIVITY_TEMPLATES.paymentProcessed('CUST-123', 299.99),
      ACTIVITY_TEMPLATES.systemAlert('Server memory usage is high', 'warning'),
      ACTIVITY_TEMPLATES.networkOutage('US-East'),
      ACTIVITY_TEMPLATES.billGenerated('CUST-456', 149.50),
    ],
  },
  parameters: {
    docs: {
      description: {
        story: 'Using built-in activity templates for consistent data.',
      },
    },
  },
};

// Portal showcase
export const AllPortalVariants: Story = {
  render: () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Admin Portal</h3>
        <ActivityFeed
          variant="admin"
          activities={generateSampleActivities().slice(0, 3)}
          config={{ maxItems: 3 }}
        />
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Customer Portal</h3>
        <ActivityFeed
          variant="customer"
          activities={[
            ACTIVITY_TEMPLATES.billGenerated('CUST-123', 49.99),
            ACTIVITY_TEMPLATES.paymentProcessed('CUST-123', 49.99),
            { ...ACTIVITY_TEMPLATES.systemAlert('Data usage at 80%', 'warning'), type: 'warning' as const }
          ]}
          config={{ maxItems: 3 }}
        />
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Reseller Portal</h3>
        <ActivityFeed
          variant="reseller"
          activities={[
            ACTIVITY_TEMPLATES.commissionEarned('RESELLER-001', 250.00),
            ACTIVITY_TEMPLATES.leadConverted('LEAD-789', 'Premium'),
            ACTIVITY_TEMPLATES.customerSignup('new.customer@biz.com', 'Business')
          ]}
          config={{ maxItems: 3 }}
        />
      </div>
    </div>
  ),
  parameters: {
    layout: 'fullscreen',
    docs: {
      description: {
        story: 'All portal variants showing consistent branding and different activity types.',
      },
    },
  },
};

// Real-time simulation
export const RealTimeSimulation: Story = {
  render: (args) => {
    const [activities, setActivities] = React.useState<Activity[]>([]);
    const [isActive, setIsActive] = React.useState(false);

    React.useEffect(() => {
      if (!isActive) return;

      const interval = setInterval(() => {
        const templates = Object.values(ACTIVITY_TEMPLATES);
        const randomTemplate = templates[Math.floor(Math.random() * templates.length)];

        let newActivity: Activity;
        if (randomTemplate === ACTIVITY_TEMPLATES.customerSignup) {
          newActivity = randomTemplate(`user${Math.floor(Math.random() * 1000)}@example.com`, 'Premium');
        } else if (randomTemplate === ACTIVITY_TEMPLATES.systemAlert) {
          newActivity = randomTemplate('Automated system alert', Math.random() > 0.5 ? 'warning' : 'error');
        } else if (randomTemplate === ACTIVITY_TEMPLATES.paymentProcessed) {
          newActivity = randomTemplate(`CUST-${Math.floor(Math.random() * 1000)}`, Math.floor(Math.random() * 500) + 50);
        } else {
          newActivity = ACTIVITY_TEMPLATES.systemAlert('Random activity', 'info');
        }

        setActivities(prev => [newActivity, ...prev].slice(0, 20));
      }, 3000);

      return () => clearInterval(interval);
    }, [isActive]);

    return (
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setIsActive(!isActive)}
            className={`px-4 py-2 rounded-md text-white font-medium ${
              isActive ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'
            }`}
          >
            {isActive ? 'Stop Simulation' : 'Start Real-time Simulation'}
          </button>
          {isActive && (
            <div className="flex items-center gap-2 text-sm text-green-600">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              Live updates every 3 seconds
            </div>
          )}
        </div>

        <ActivityFeed
          {...args}
          activities={activities}
          variant="admin"
          config={{ maxItems: 10 }}
        />
      </div>
    );
  },
  parameters: {
    docs: {
      description: {
        story: 'Real-time activity simulation showing live updates.',
      },
    },
  },
};

// Accessibility showcase
export const AccessibilityShowcase: Story = {
  render: () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Proper Semantics</h3>
        <ActivityFeed
          variant="admin"
          activities={generateSampleActivities().slice(0, 3)}
          config={{ maxItems: 3 }}
          onActivityClick={(activity) => console.log('Activity clicked:', activity.title)}
        />
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-medium text-blue-900 mb-2">Accessibility Features</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Semantic HTML structure with proper ARIA roles</li>
          <li>• Keyboard navigation support for interactive elements</li>
          <li>• High contrast color combinations for all activity types</li>
          <li>• Screen reader friendly time stamps and descriptions</li>
          <li>• Focus management for expandable content</li>
        </ul>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates accessibility features and proper ARIA usage.',
      },
    },
    a11y: {
      config: {
        rules: [
          { id: 'color-contrast', enabled: true },
          { id: 'button-name', enabled: true },
          { id: 'list', enabled: true },
          { id: 'heading-order', enabled: true },
        ],
      },
    },
  },
};
