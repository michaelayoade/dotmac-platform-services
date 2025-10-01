/**
 * Universal Dashboard Demo
 * Example implementation showing how to use Universal Dashboard Components
 */

'use client';

import React from 'react';
import {
  Users,
  DollarSign,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Settings,
  Download,
  RefreshCw,
} from 'lucide-react';

import { UniversalDashboard } from './UniversalDashboard';
import { UniversalKPISection } from './UniversalKPISection';
import { UniversalActivityFeed } from './UniversalActivityFeed';

// Example data for demonstration
const demoUser = {
  id: '1',
  name: 'John Smith',
  email: 'john.smith@example.com',
  role: 'Admin',
  avatar:
    'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=32&h=32&fit=crop&crop=face',
};

const demoTenant = {
  id: 'tenant-1',
  name: 'Demo ISP',
  companyName: 'Demo Internet Service Provider',
  plan: 'Enterprise',
  status: 'active' as const,
};

const demoKPIs = [
  {
    id: 'customers',
    title: 'Total Customers',
    value: 15420,
    format: 'number' as const,
    icon: Users,
    trend: {
      direction: 'up' as const,
      percentage: 12.5,
      label: 'vs last month',
    },
    progress: {
      current: 15420,
      target: 20000,
      label: 'Growth Target',
    },
    status: {
      type: 'success' as const,
    },
  },
  {
    id: 'revenue',
    title: 'Monthly Revenue',
    value: 89650,
    format: 'currency' as const,
    currency: 'USD',
    icon: DollarSign,
    trend: {
      direction: 'up' as const,
      percentage: 8.2,
      label: 'vs last month',
    },
    status: {
      type: 'success' as const,
    },
  },
  {
    id: 'growth',
    title: 'Growth Rate',
    value: 15.8,
    format: 'percentage' as const,
    precision: 1,
    icon: TrendingUp,
    trend: {
      direction: 'up' as const,
      percentage: 2.1,
      label: 'vs last quarter',
    },
    status: {
      type: 'info' as const,
    },
  },
  {
    id: 'issues',
    title: 'Open Issues',
    value: 23,
    format: 'number' as const,
    icon: AlertTriangle,
    trend: {
      direction: 'down' as const,
      percentage: -18.5,
      label: 'vs last week',
    },
    status: {
      type: 'warning' as const,
      label: 'Needs attention',
    },
  },
];

const demoActivities = [
  {
    id: '1',
    type: 'user_action' as const,
    title: 'New customer onboarded',
    description: 'Sarah Johnson signed up for Fiber Pro plan',
    timestamp: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
    user: {
      id: 'u1',
      name: 'Sales Team',
      avatar:
        'https://images.unsplash.com/photo-1494790108755-2616b2e83e0f?w=24&h=24&fit=crop&crop=face',
    },
    category: 'Sales',
  },
  {
    id: '2',
    type: 'system_event' as const,
    title: 'Network maintenance completed',
    description: 'Router firmware updates applied successfully',
    timestamp: new Date(Date.now() - 20 * 60 * 1000), // 20 minutes ago
    category: 'Network',
  },
  {
    id: '3',
    type: 'success' as const,
    title: 'Payment processed',
    description: '$89.99 monthly subscription payment received',
    timestamp: new Date(Date.now() - 45 * 60 * 1000), // 45 minutes ago
    category: 'Billing',
  },
  {
    id: '4',
    type: 'warning' as const,
    title: 'High bandwidth usage detected',
    description: 'Customer ID #4521 approaching data limit',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
    category: 'Network',
    priority: 'medium' as const,
  },
  {
    id: '5',
    type: 'error' as const,
    title: 'Service outage reported',
    description: 'Connection issues in downtown area - investigating',
    timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000), // 3 hours ago
    category: 'Support',
    priority: 'high' as const,
  },
];

export function AdminDashboardDemo() {
  return (
    <UniversalDashboard
      variant='admin'
      user={demoUser}
      tenant={demoTenant}
      title={`Welcome back, ${demoUser.name}!`}
      subtitle="Here's what's happening with your ISP operations today"
      actions={[
        {
          id: 'export',
          label: 'Export Report',
          icon: Download,
          onClick: () => console.log('Export clicked'),
          variant: 'outline',
        },
        {
          id: 'refresh',
          label: 'Refresh',
          icon: RefreshCw,
          onClick: () => console.log('Refresh clicked'),
          variant: 'secondary',
        },
        {
          id: 'settings',
          label: 'Settings',
          icon: Settings,
          onClick: () => console.log('Settings clicked'),
          variant: 'primary',
        },
      ]}
    >
      {/* KPIs Section */}
      <UniversalKPISection
        title='Key Performance Indicators'
        subtitle='Your business metrics at a glance'
        kpis={demoKPIs}
        columns={4}
        responsiveColumns={{ sm: 1, md: 2, lg: 4 }}
      />

      {/* Activity Feed */}
      <UniversalActivityFeed
        title='Recent Activity'
        activities={demoActivities}
        maxItems={5}
        showTimestamps={true}
        showAvatars={true}
        showCategories={true}
        allowFiltering={true}
        categories={['Sales', 'Network', 'Billing', 'Support']}
        isLive={true}
        refreshInterval={30}
        onRefresh={() => console.log('Refreshing activities...')}
      />
    </UniversalDashboard>
  );
}

export function ResellerDashboardDemo() {
  const resellerKPIs = [
    {
      id: 'commissions',
      title: 'Monthly Commissions',
      value: 12850,
      format: 'currency' as const,
      icon: DollarSign,
      trend: { direction: 'up' as const, percentage: 15.2, label: 'vs last month' },
      status: { type: 'success' as const },
    },
    {
      id: 'customers',
      title: 'Active Customers',
      value: 287,
      format: 'number' as const,
      icon: Users,
      progress: { current: 287, target: 500, label: 'Target' },
      status: { type: 'info' as const },
    },
  ];

  return (
    <UniversalDashboard
      variant='reseller'
      user={demoUser}
      title='Reseller Portal'
      subtitle='Track your sales performance and commissions'
    >
      <UniversalKPISection
        title='Sales Performance'
        kpis={resellerKPIs}
        columns={2}
        responsiveColumns={{ sm: 1, md: 2 }}
      />
    </UniversalDashboard>
  );
}

export function CustomerDashboardDemo() {
  const customerKPIs = [
    {
      id: 'usage',
      title: 'Data Usage',
      value: 425,
      format: 'bytes' as const,
      suffix: ' GB',
      icon: TrendingUp,
      progress: { current: 425, target: 1000, label: 'Monthly Limit' },
      status: { type: 'info' as const },
    },
  ];

  return (
    <UniversalDashboard
      variant='customer'
      user={demoUser}
      title='My Account'
      subtitle='Manage your internet service'
    >
      <UniversalKPISection title='Usage & Billing' kpis={customerKPIs} columns={1} />
    </UniversalDashboard>
  );
}

// Export all demos
export default {
  AdminDashboardDemo,
  ResellerDashboardDemo,
  CustomerDashboardDemo,
};
