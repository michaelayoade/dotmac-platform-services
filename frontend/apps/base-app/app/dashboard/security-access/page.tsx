'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Shield,
  Key,
  Lock,
  Users,
  UserCheck,
  AlertTriangle,
  ArrowUpRight,
  Activity,
  Eye,
  FileWarning
} from 'lucide-react';
import { metricsService, SecurityMetrics } from '@/lib/services/metrics-service';
import { AlertBanner } from '@/components/alerts/AlertBanner';
import { apiClient } from '@/lib/api/client';

interface SecurityMetric {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ElementType;
  status?: 'success' | 'warning' | 'danger';
  href?: string;
}

function SecurityMetricCard({ title, value, subtitle, icon: Icon, status = 'success', href }: SecurityMetric) {
  const statusColors = {
    success: 'text-green-400 bg-green-400/10',
    warning: 'text-yellow-400 bg-yellow-400/10',
    danger: 'text-red-400 bg-red-400/10'
  };

  const content = (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-6 hover:border-slate-700 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-slate-400">{title}</p>
          <p className="mt-2 text-3xl font-bold text-white">{value}</p>
          {subtitle && (
            <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${statusColors[status]}`}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="block group relative">
        {content}
        <ArrowUpRight className="absolute top-4 right-4 h-4 w-4 text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity" />
      </Link>
    );
  }

  return content;
}

interface SecurityEvent {
  id: string;
  type: 'auth_success' | 'auth_failure' | 'permission_change' | 'api_key_created' | 'secret_accessed';
  description: string;
  user?: string;
  timestamp: string;
  severity: 'info' | 'warning' | 'critical';
}

function SecurityEventLog({ events }: { events: SecurityEvent[] }) {
  const severityColors = {
    info: 'text-blue-400',
    warning: 'text-yellow-400',
    critical: 'text-red-400'
  };

  const typeIcons = {
    auth_success: UserCheck,
    auth_failure: AlertTriangle,
    permission_change: Shield,
    api_key_created: Key,
    secret_accessed: Eye
  };

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900">
      <div className="p-6 border-b border-slate-800 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Security Events</h3>
        <Link href="/dashboard/security-access/audit" className="text-sm text-sky-400 hover:text-sky-300">
          View all →
        </Link>
      </div>
      <div className="divide-y divide-slate-800 max-h-96 overflow-y-auto">
        {events.length === 0 ? (
          <div className="p-6 text-center text-slate-500">
            No recent security events
          </div>
        ) : (
          events.map((event) => {
            const Icon = typeIcons[event.type];
            return (
              <div key={event.id} className="p-4 hover:bg-slate-800/50 transition-colors">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-slate-800 rounded-lg">
                    <Icon className={`h-4 w-4 ${severityColors[event.severity]}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-white">{event.description}</p>
                    {event.user && (
                      <p className="text-sm text-slate-400 mt-1">User: {event.user}</p>
                    )}
                  </div>
                  <span className="text-xs text-slate-500 whitespace-nowrap">
                    {event.timestamp}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

interface AccessControlSummary {
  totalUsers: number;
  activeUsers: number;
  totalRoles: number;
  apiKeys: number;
  secrets: number;
  mfaEnabled: number;
}

function AccessControlPanel({ data }: { data: AccessControlSummary }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Access Control Summary</h3>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Users className="h-5 w-5 text-slate-400" />
            <span className="text-slate-300">Total Users</span>
          </div>
          <span className="font-medium text-white">{data.totalUsers}</span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <UserCheck className="h-5 w-5 text-slate-400" />
            <span className="text-slate-300">Active Users</span>
          </div>
          <span className="font-medium text-white">{data.activeUsers}</span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="h-5 w-5 text-slate-400" />
            <span className="text-slate-300">Roles Configured</span>
          </div>
          <span className="font-medium text-white">{data.totalRoles}</span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Key className="h-5 w-5 text-slate-400" />
            <span className="text-slate-300">API Keys</span>
          </div>
          <span className="font-medium text-white">{data.apiKeys}</span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Lock className="h-5 w-5 text-slate-400" />
            <span className="text-slate-300">Secrets Stored</span>
          </div>
          <span className="font-medium text-white">{data.secrets}</span>
        </div>
        <div className="border-t border-slate-800 pt-4 mt-4">
          <div className="flex items-center justify-between">
            <span className="text-slate-300">MFA Adoption</span>
            <div className="flex items-center gap-2">
              <div className="w-32 h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500 rounded-full"
                  style={{ width: `${(data.mfaEnabled / data.totalUsers) * 100}%` }}
                />
              </div>
              <span className="text-sm text-slate-400">
                {Math.round((data.mfaEnabled / data.totalUsers) * 100)}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function SecurityAccessPage() {
  const [metrics, setMetrics] = useState<SecurityMetrics | null>(null);
  const [accessControlData, setAccessControlData] = useState<AccessControlSummary | null>(null);
  const [recentEvents, setRecentEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSecurityData();
    // Refresh metrics every 60 seconds
    const interval = setInterval(fetchSecurityData, 60000);
    return () => clearInterval(interval);
  }, []);

  const fetchSecurityData = async () => {
    try {
      setLoading(true);

      // Fetch security metrics from the metrics service
      const securityMetrics = await metricsService.getSecurityMetrics();
      setMetrics(securityMetrics);

      // Calculate access control summary from metrics
      const totalUsers = securityMetrics.auth.activeSessions || 0;
      setAccessControlData({
        totalUsers: totalUsers,
        activeUsers: securityMetrics.auth.activeSessions || 0,
        totalRoles: 12, // This would come from a roles API
        apiKeys: securityMetrics.apiKeys.total || 0,
        secrets: securityMetrics.secrets.total || 0,
        mfaEnabled: securityMetrics.auth.mfaEnabled || 0
      });

      // Fetch recent audit events
      try {
        const eventsResponse = await apiClient.get<Array<Record<string, unknown>>>('/api/v1/audit/events?limit=10');
        if (eventsResponse.success && eventsResponse.data) {
          const events: SecurityEvent[] = eventsResponse.data.map((e, index: number) => {
            const eventType = e.type as string;
            const validTypes: SecurityEvent['type'][] = ['auth_success', 'auth_failure', 'permission_change', 'api_key_created', 'secret_accessed'];
            const type: SecurityEvent['type'] = validTypes.includes(eventType as SecurityEvent['type'])
              ? (eventType as SecurityEvent['type'])
              : 'auth_success';

            const eventSeverity = e.severity as string;
            const validSeverities: SecurityEvent['severity'][] = ['info', 'warning', 'critical'];
            const severity: SecurityEvent['severity'] = validSeverities.includes(eventSeverity as SecurityEvent['severity'])
              ? (eventSeverity as SecurityEvent['severity'])
              : 'info';

            return {
              id: (e.id as string) || `event-${index}`,
              type,
              description: (e.description as string) || (e.message as string) || 'Security event',
              user: (e.user_email as string) || (e.user_id as string),
              timestamp: e.created_at ? new Date(e.created_at as string).toLocaleString() : 'Recently',
              severity
            };
          });
          setRecentEvents(events);
        }
      } catch (err) {
        // Fallback to showing metrics-based events
        const fallbackEvents: SecurityEvent[] = [];

        if (securityMetrics.auth.failedAttempts > 0) {
          fallbackEvents.push({
            id: 'auth-failures',
            type: 'auth_failure',
            description: `${securityMetrics.auth.failedAttempts} failed login attempts`,
            timestamp: 'Recent',
            severity: 'warning'
          });
        }

        if (securityMetrics.apiKeys.expiring > 0) {
          fallbackEvents.push({
            id: 'api-keys-expiring',
            type: 'api_key_created',
            description: `${securityMetrics.apiKeys.expiring} API keys expiring soon`,
            timestamp: 'This week',
            severity: 'info'
          });
        }

        if (securityMetrics.secrets.expired > 0) {
          fallbackEvents.push({
            id: 'secrets-expired',
            type: 'secret_accessed',
            description: `${securityMetrics.secrets.expired} secrets have expired`,
            timestamp: 'Current',
            severity: 'critical'
          });
        }

        setRecentEvents(fallbackEvents);
      }
    } catch (err) {
      console.error('Failed to fetch security metrics:', err);
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Security & Access</h1>
        <p className="mt-2 text-slate-400">
          Manage API keys, secrets, roles, and user access control
        </p>
      </div>

      {/* Alert Banner - Shows security-related alerts */}
      <AlertBanner category="security" maxAlerts={3} />

      {/* Security Alerts based on metrics */}
      {metrics && metrics.auth.failedAttempts > 5 && (
        <div className="rounded-lg border border-orange-900/20 bg-orange-950/20 p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-orange-400 mt-0.5" />
            <div className="flex-1">
              <p className="font-medium text-orange-400">Security Alert</p>
              <p className="mt-1 text-sm text-slate-400">
                {metrics.auth.failedAttempts} failed authentication attempts detected.
                <Link href="/dashboard/security-access/audit" className="ml-2 text-orange-400 hover:text-orange-300">
                  Review security logs →
                </Link>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <SecurityMetricCard
          title="Security Score"
          value={`${metrics?.compliance.score || 0}/100`}
          subtitle={`${metrics?.compliance.issues || 0} issues`}
          icon={Shield}
          status={metrics?.compliance.score && metrics.compliance.score > 80 ? 'success' : 'warning'}
        />
        <SecurityMetricCard
          title="Active Sessions"
          value={metrics?.auth.activeSessions || 0}
          subtitle={`${metrics?.auth.passwordResets || 0} password resets`}
          icon={Users}
          status="success"
          href="/dashboard/security-access/users"
        />
        <SecurityMetricCard
          title="API Keys"
          value={metrics?.apiKeys.total || 0}
          subtitle={`${metrics?.apiKeys.expiring || 0} expiring soon`}
          icon={Key}
          status={metrics?.apiKeys.expiring && metrics.apiKeys.expiring > 0 ? 'warning' : 'success'}
          href="/dashboard/security-access/api-keys"
        />
        <SecurityMetricCard
          title="Secrets"
          value={metrics?.secrets.total || 0}
          subtitle={`${metrics?.secrets.rotated || 0} rotated recently`}
          icon={Lock}
          status={metrics?.secrets.expired && metrics.secrets.expired > 0 ? 'danger' : 'success'}
          href="/dashboard/security-access/secrets"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          {/* Security Events */}
          <SecurityEventLog events={recentEvents} />

          {/* Quick Actions */}
          <div>
            <h2 className="text-xl font-semibold text-white mb-4">Security Management</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Link
                href="/dashboard/security-access/api-keys"
                className="flex items-center gap-4 rounded-lg border border-slate-800 bg-slate-900 p-4 hover:border-slate-700 transition-colors"
              >
                <div className="p-2 bg-slate-800 rounded-lg">
                  <Key className="h-5 w-5 text-sky-400" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-white">API Keys</p>
                  <p className="text-sm text-slate-400">Manage API access</p>
                </div>
                <ArrowUpRight className="h-4 w-4 text-slate-500" />
              </Link>

              <Link
                href="/dashboard/security-access/secrets"
                className="flex items-center gap-4 rounded-lg border border-slate-800 bg-slate-900 p-4 hover:border-slate-700 transition-colors"
              >
                <div className="p-2 bg-slate-800 rounded-lg">
                  <Lock className="h-5 w-5 text-sky-400" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-white">Secrets Vault</p>
                  <p className="text-sm text-slate-400">Secure credentials</p>
                </div>
                <ArrowUpRight className="h-4 w-4 text-slate-500" />
              </Link>

              <Link
                href="/dashboard/security-access/roles"
                className="flex items-center gap-4 rounded-lg border border-slate-800 bg-slate-900 p-4 hover:border-slate-700 transition-colors"
              >
                <div className="p-2 bg-slate-800 rounded-lg">
                  <Shield className="h-5 w-5 text-sky-400" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-white">Roles & Permissions</p>
                  <p className="text-sm text-slate-400">Access control</p>
                </div>
                <ArrowUpRight className="h-4 w-4 text-slate-500" />
              </Link>

              <Link
                href="/dashboard/security-access/users"
                className="flex items-center gap-4 rounded-lg border border-slate-800 bg-slate-900 p-4 hover:border-slate-700 transition-colors"
              >
                <div className="p-2 bg-slate-800 rounded-lg">
                  <Users className="h-5 w-5 text-sky-400" />
                </div>
                <div className="flex-1">
                  <p className="font-medium text-white">User Management</p>
                  <p className="text-sm text-slate-400">Users and teams</p>
                </div>
                <ArrowUpRight className="h-4 w-4 text-slate-500" />
              </Link>
            </div>
          </div>
        </div>

        {/* Access Control Summary */}
        <div className="lg:col-span-1">
          {accessControlData && <AccessControlPanel data={accessControlData} />}
        </div>
      </div>
    </div>
  );
}