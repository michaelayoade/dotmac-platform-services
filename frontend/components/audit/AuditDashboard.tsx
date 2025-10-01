import React, { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import {
  Activity,
  TrendingUp,
  AlertCircle,
  Shield,
  Users,
  Lock,
  FileText,
  Globe
} from 'lucide-react';

// Types
interface AuditSummary {
  period_days: number;
  total_activities: number;
  activities_by_type: Record<string, number>;
  activities_by_severity: Record<string, number>;
  since_date: string;
}

interface DashboardStats {
  title: string;
  value: number | string;
  change?: number;
  icon: React.ElementType;
  color: string;
}

// Colors for charts
const SEVERITY_COLORS = {
  LOW: '#10b981',
  MEDIUM: '#f59e0b',
  HIGH: '#f97316',
  CRITICAL: '#ef4444'
};

const TYPE_COLORS = [
  '#3b82f6', // blue
  '#8b5cf6', // violet
  '#06b6d4', // cyan
  '#10b981', // emerald
  '#f59e0b', // amber
  '#ef4444', // red
  '#6366f1', // indigo
  '#ec4899', // pink
];

// Stat Card Component
const StatCard: React.FC<DashboardStats> = ({ title, value, change, icon: Icon, color }) => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {change !== undefined && (
            <div className="flex items-center mt-2">
              <TrendingUp className={`w-4 h-4 ${change >= 0 ? 'text-green-500' : 'text-red-500'} mr-1`} />
              <span className={`text-sm ${change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {change >= 0 ? '+' : ''}{change}%
              </span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-full ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );
};

// Activity Timeline Component
const ActivityTimeline: React.FC<{ activities: any[] }> = ({ activities }) => {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-medium text-gray-900 mb-4">Activity Timeline</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={activities}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

// Main Dashboard Component
export const AuditDashboard: React.FC = () => {
  const [summary, setSummary] = useState<AuditSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState(7);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`/api/v1/audit/activities/summary?days=${timeRange}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch audit summary');
        }

        const data = await response.json();
        setSummary(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, [timeRange]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 rounded-lg">
        <div className="flex items-center">
          <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
          <p className="text-sm text-red-600">Error loading dashboard: {error}</p>
        </div>
      </div>
    );
  }

  if (!summary) return null;

  // Calculate stats
  const criticalActivities = summary.activities_by_severity['CRITICAL'] || 0;
  const highActivities = summary.activities_by_severity['HIGH'] || 0;
  const userActivities = (summary.activities_by_type['user.login'] || 0) +
                        (summary.activities_by_type['user.created'] || 0);
  const secretActivities = (summary.activities_by_type['secret.accessed'] || 0) +
                          (summary.activities_by_type['secret.created'] || 0) +
                          (summary.activities_by_type['secret.deleted'] || 0);

  const stats: DashboardStats[] = [
    {
      title: 'Total Activities',
      value: summary.total_activities.toLocaleString(),
      icon: Activity,
      color: 'bg-blue-500',
    },
    {
      title: 'Critical Events',
      value: criticalActivities,
      icon: AlertCircle,
      color: criticalActivities > 0 ? 'bg-red-500' : 'bg-gray-500',
    },
    {
      title: 'User Activities',
      value: userActivities,
      icon: Users,
      color: 'bg-green-500',
    },
    {
      title: 'Secret Operations',
      value: secretActivities,
      icon: Lock,
      color: 'bg-purple-500',
    },
  ];

  // Prepare chart data
  const severityData = Object.entries(summary.activities_by_severity).map(([severity, count]) => ({
    name: severity,
    value: count,
  }));

  const typeData = Object.entries(summary.activities_by_type)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([type, count]) => ({
      name: type.split('.').pop(),
      value: count,
    }));

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Audit Dashboard</h1>
          <p className="text-gray-600 mt-2">Monitor system activities and security events</p>
        </div>

        {/* Time Range Selector */}
        <div className="mb-6 flex space-x-2">
          {[1, 7, 30, 90].map((days) => (
            <button
              key={days}
              onClick={() => setTimeRange(days)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                timeRange === days
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {days === 1 ? '24h' : `${days}d`}
            </button>
          ))}
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
          {stats.map((stat) => (
            <StatCard key={stat.title} {...stat} />
          ))}
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Activities by Type */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Activities by Type</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={typeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Activities by Severity */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Activities by Severity</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {severityData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={SEVERITY_COLORS[entry.name as keyof typeof SEVERITY_COLORS] || '#888'} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Security Alerts */}
        {(criticalActivities > 0 || highActivities > 0) && (
          <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-center">
              <Shield className="w-6 h-6 text-red-600 mr-3" />
              <div>
                <h3 className="text-lg font-medium text-red-900">Security Alerts</h3>
                <p className="text-red-700 mt-1">
                  {criticalActivities > 0 && `${criticalActivities} critical events detected. `}
                  {highActivities > 0 && `${highActivities} high severity events require attention.`}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuditDashboard;