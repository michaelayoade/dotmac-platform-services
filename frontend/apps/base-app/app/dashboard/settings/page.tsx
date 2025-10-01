'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  User,
  Users,
  CreditCard,
  Mail,
  Lock,
  Bell,
  Shield,
  Globe,
  Palette,
  Database,
  Key,
  Package,
  Building,
  ArrowUpRight,
  Settings as SettingsIcon,
  Sliders,
  FileText,
  Zap,
  Cloud,
  Smartphone
} from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { RouteGuard } from '@/components/auth/PermissionGuard';

interface SettingCard {
  id: string;
  title: string;
  description: string;
  icon: React.ElementType;
  href: string;
  status?: 'active' | 'warning' | 'info';
  badge?: string;
}

const settingCards: SettingCard[] = [
  {
    id: 'profile',
    title: 'Profile',
    description: 'Manage your personal information and account details',
    icon: User,
    href: '/dashboard/settings/profile',
    status: 'active'
  },
  {
    id: 'organization',
    title: 'Organization',
    description: 'Company information, team management, and roles',
    icon: Building,
    href: '/dashboard/settings/organization'
  },
  {
    id: 'billing',
    title: 'Billing Preferences',
    description: 'Payment methods, billing address, and invoice settings',
    icon: CreditCard,
    href: '/dashboard/settings/billing',
    badge: 'Payment due'
  },
  {
    id: 'notifications',
    title: 'Notifications',
    description: 'Email alerts, push notifications, and communication preferences',
    icon: Bell,
    href: '/dashboard/settings/notifications'
  },
  {
    id: 'security',
    title: 'Security',
    description: 'Password, two-factor authentication, and security settings',
    icon: Shield,
    href: '/dashboard/settings/security',
    status: 'warning',
    badge: 'MFA disabled'
  },
  {
    id: 'integrations',
    title: 'Integrations',
    description: 'Connect with third-party services and APIs',
    icon: Package,
    href: '/dashboard/settings/integrations'
  },
  {
    id: 'api-tokens',
    title: 'API Tokens',
    description: 'Manage personal API access tokens and OAuth apps',
    icon: Key,
    href: '/dashboard/settings/tokens'
  },
  {
    id: 'appearance',
    title: 'Appearance',
    description: 'Theme preferences, display settings, and UI customization',
    icon: Palette,
    href: '/dashboard/settings/appearance'
  },
  {
    id: 'data-privacy',
    title: 'Data & Privacy',
    description: 'Data export, deletion requests, and privacy controls',
    icon: Database,
    href: '/dashboard/settings/privacy'
  },
  {
    id: 'advanced',
    title: 'Advanced',
    description: 'Developer settings, experimental features, and system config',
    icon: Sliders,
    href: '/dashboard/settings/advanced'
  },
];

interface QuickStat {
  label: string;
  value: string | number;
  icon: React.ElementType;
  trend?: 'up' | 'down' | 'stable';
}

function QuickStats({ stats }: { stats: QuickStat[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, index) => (
        <div key={index} className="rounded-lg border border-slate-800 bg-slate-900 p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">{stat.label}</p>
              <p className="mt-1 text-2xl font-semibold text-white">{stat.value}</p>
            </div>
            <div className="p-2 bg-slate-800 rounded-lg">
              <stat.icon className="h-5 w-5 text-sky-400" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function SettingCard({ card }: { card: SettingCard }) {
  const statusColors = {
    active: 'border-green-900/20 bg-green-950/10',
    warning: 'border-orange-900/20 bg-orange-950/10',
    info: 'border-blue-900/20 bg-blue-950/10'
  };

  const badgeColors = {
    active: 'bg-green-500/20 text-green-400',
    warning: 'bg-orange-500/20 text-orange-400',
    info: 'bg-blue-500/20 text-blue-400'
  };

  return (
    <Link
      href={card.href}
      className={`group relative rounded-lg border p-6 hover:border-slate-700 transition-all ${
        card.status ? statusColors[card.status] : 'border-slate-800 bg-slate-900 hover:bg-slate-800/50'
      }`}
    >
      <div className="flex items-start gap-4">
        <div className="p-3 bg-slate-800 rounded-lg group-hover:bg-slate-700 transition-colors">
          <card.icon className="h-6 w-6 text-sky-400" />
        </div>
        <div className="flex-1">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold text-white group-hover:text-sky-400 transition-colors">
                {card.title}
              </h3>
              <p className="mt-1 text-sm text-slate-400">
                {card.description}
              </p>
            </div>
            <ArrowUpRight className="h-4 w-4 text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
          {card.badge && (
            <span className={`inline-block mt-3 px-2 py-1 text-xs font-medium rounded-full ${
              card.status ? badgeColors[card.status] : 'bg-slate-700 text-slate-300'
            }`}>
              {card.badge}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}

function SettingsHubPageContent() {
  const [user, setUser] = useState<Record<string, unknown> | null>(null);
  const [organization, setOrganization] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSettingsData();
  }, []);

  const fetchSettingsData = async () => {
    try {
      setLoading(true);
      // Fetch user and organization data
      const [userResponse, orgResponse] = await Promise.all([
        apiClient.get('/api/v1/auth/me').catch(() => ({ success: false })),
        apiClient.get('/api/v1/organization').catch(() => ({ success: false }))
      ]);

      if (userResponse.success && 'data' in userResponse) {
        setUser(userResponse.data as Record<string, unknown>);
      }
      if (orgResponse.success && 'data' in orgResponse) {
        setOrganization(orgResponse.data as Record<string, unknown>);
      }
    } catch (err) {
      console.error('Failed to fetch settings data:', err);
    } finally {
      setLoading(false);
    }
  };

  const quickStats: QuickStat[] = [
    { label: 'Active Sessions', value: 3, icon: Smartphone },
    { label: 'API Calls Today', value: '1,234', icon: Zap },
    { label: 'Storage Used', value: '2.3 GB', icon: Cloud },
    { label: 'Team Members', value: (organization?.memberCount as number) || 5, icon: Users }
  ];

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div>
          <div className="flex items-center gap-3 mb-2">
            <SettingsIcon className="h-8 w-8 text-sky-400" />
            <h1 className="text-3xl font-bold text-white">Settings</h1>
          </div>
          <p className="text-slate-400">
            Manage your account, organization, and platform preferences
          </p>
        </div>

        {/* Quick Stats */}
        <QuickStats stats={quickStats} />

        {/* User Info Banner */}
        {user && (
          <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-gradient-to-br from-sky-400 to-blue-500 flex items-center justify-center text-white font-semibold text-lg">
                  {(user.username as string)?.charAt(0).toUpperCase() || 'U'}
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-white">{(user.full_name || user.username) as string}</h2>
                  <p className="text-sm text-slate-400">{user.email as string}</p>
                  <p className="text-xs text-slate-500 mt-1">
                    Organization: {(organization?.name as string) || 'Personal'} •
                    Plan: {(organization?.plan as string) || 'Free'} •
                    Role: {(user.roles as string[])?.join(', ') || 'User'}
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                <Link
                  href="/dashboard/settings/profile"
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  Edit Profile
                </Link>
                <Link
                  href="/dashboard/settings/security"
                  className="px-4 py-2 bg-sky-500 hover:bg-sky-600 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  Security Settings
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Settings Categories */}
        <div>
          <h2 className="text-xl font-semibold text-white mb-4">Configuration Areas</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {settingCards.map((card) => (
              <SettingCard key={card.id} card={card} />
            ))}
          </div>
        </div>

        {/* Quick Links */}
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Link
              href="/dashboard/settings/security#change-password"
              className="flex items-center gap-2 text-sm text-slate-400 hover:text-sky-400 transition-colors"
            >
              <Lock className="h-4 w-4" />
              Change Password
            </Link>
            <Link
              href="/dashboard/settings/security#2fa"
              className="flex items-center gap-2 text-sm text-slate-400 hover:text-sky-400 transition-colors"
            >
              <Shield className="h-4 w-4" />
              Enable 2FA
            </Link>
            <Link
              href="/dashboard/settings/privacy#export"
              className="flex items-center gap-2 text-sm text-slate-400 hover:text-sky-400 transition-colors"
            >
              <Database className="h-4 w-4" />
              Export Data
            </Link>
            <Link
              href="/dashboard/settings/billing"
              className="flex items-center gap-2 text-sm text-slate-400 hover:text-sky-400 transition-colors"
            >
              <CreditCard className="h-4 w-4" />
              Update Payment
            </Link>
          </div>
        </div>

        {/* Help Section */}
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
          <h3 className="text-lg font-semibold text-white mb-2">Need Help?</h3>
          <p className="text-sm text-slate-400 mb-4">
            Check out our documentation or contact support for assistance with your settings.
          </p>
          <div className="flex gap-3">
            <Link
              href="/docs/settings"
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm font-medium transition-colors"
            >
              <FileText className="inline h-4 w-4 mr-2" />
              Documentation
            </Link>
            <Link
              href="/support"
              className="px-4 py-2 border border-slate-700 hover:bg-slate-800 text-white rounded-lg text-sm font-medium transition-colors"
            >
              <Mail className="inline h-4 w-4 mr-2" />
              Contact Support
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function SettingsHubPage() {
  return (
    <RouteGuard permission="settings.read">
      <SettingsHubPageContent />
    </RouteGuard>
  );
}