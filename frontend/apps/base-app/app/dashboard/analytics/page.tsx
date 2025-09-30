'use client';

import { useState, useEffect } from 'react';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  Users,
  Server,
  Database,
  Clock,
  BarChart3,
  PieChart,
  Filter,
  Download,
  RefreshCw
} from 'lucide-react';
import { platformConfig } from '@/lib/config';

interface AnalyticsData {
  user_activity: {
    total_requests: number;
    unique_users: number;
    avg_response_time: number;
    error_rate: number;
  };
  system_metrics: {
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
    active_connections: number;
  };
  api_endpoints: Array<{
    endpoint: string;
    requests: number;
    avg_response_time: number;
    error_count: number;
  }>;
  time_series?: Array<{
    timestamp: string;
    requests: number;
    errors: number;
    response_time: number;
  }>;
}

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('24h');
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    try {
      setRefreshing(true);
      const response = await fetch(`${platformConfig.apiBaseUrl}/api/v1/analytics?range=${timeRange}`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      } else if (response.status === 401) {
        window.location.href = '/login';
      } else {
        console.error('Failed to fetch analytics:', response.status);
        // Use mock data for demo
        setAnalytics({
          user_activity: {
            total_requests: 12847,
            unique_users: 324,
            avg_response_time: 145,
            error_rate: 0.02
          },
          system_metrics: {
            cpu_usage: 67,
            memory_usage: 78,
            disk_usage: 45,
            active_connections: 156
          },
          api_endpoints: [
            { endpoint: '/api/v1/auth/login', requests: 2456, avg_response_time: 89, error_count: 12 },
            { endpoint: '/api/v1/users/me', requests: 3421, avg_response_time: 56, error_count: 3 },
            { endpoint: '/api/v1/customers', requests: 1876, avg_response_time: 123, error_count: 8 },
            { endpoint: '/api/v1/secrets', requests: 567, avg_response_time: 234, error_count: 2 },
            { endpoint: '/api/v1/analytics', requests: 234, avg_response_time: 178, error_count: 1 }
          ]
        });
      }
    } catch (error) {
      console.error('Error fetching analytics:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  const getPercentageColor = (percentage: number) => {
    if (percentage >= 80) return 'text-red-600 bg-red-100';
    if (percentage >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  if (loading && !analytics) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!analytics) return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600">Monitor system performance and user activity</p>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="1h">Last Hour</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          <button
            onClick={fetchAnalytics}
            disabled={refreshing}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* User Activity Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Activity className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Requests</p>
              <p className="text-2xl font-bold text-gray-900">{formatNumber(analytics.user_activity.total_requests)}</p>
              <div className="flex items-center mt-1">
                <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                <span className="text-sm text-green-600">+12.5%</span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Users className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Unique Users</p>
              <p className="text-2xl font-bold text-gray-900">{formatNumber(analytics.user_activity.unique_users)}</p>
              <div className="flex items-center mt-1">
                <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
                <span className="text-sm text-green-600">+8.3%</span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Clock className="h-8 w-8 text-yellow-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Avg Response Time</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.user_activity.avg_response_time}ms</p>
              <div className="flex items-center mt-1">
                <TrendingDown className="h-4 w-4 text-green-500 mr-1" />
                <span className="text-sm text-green-600">-5.2%</span>
              </div>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Activity className="h-8 w-8 text-red-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Error Rate</p>
              <p className="text-2xl font-bold text-gray-900">{(analytics.user_activity.error_rate * 100).toFixed(2)}%</p>
              <div className="flex items-center mt-1">
                <TrendingDown className="h-4 w-4 text-green-500 mr-1" />
                <span className="text-sm text-green-600">-0.5%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* System Metrics */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">System Resources</h2>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="relative">
                <svg className="w-20 h-20 mx-auto">
                  <circle
                    cx="40"
                    cy="40"
                    r="32"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                    className="text-gray-200"
                  />
                  <circle
                    cx="40"
                    cy="40"
                    r="32"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                    strokeDasharray={2 * Math.PI * 32}
                    strokeDashoffset={2 * Math.PI * 32 * (1 - analytics.system_metrics.cpu_usage / 100)}
                    className="text-blue-600"
                    transform="rotate(-90 40 40)"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-sm font-semibold text-gray-900">{analytics.system_metrics.cpu_usage}%</span>
                </div>
              </div>
              <p className="mt-2 text-sm font-medium text-gray-900">CPU Usage</p>
              <div className="flex items-center justify-center mt-1">
                <Server className="h-4 w-4 text-gray-400 mr-1" />
                <span className="text-xs text-gray-500">4 cores</span>
              </div>
            </div>
            <div className="text-center">
              <div className="relative">
                <svg className="w-20 h-20 mx-auto">
                  <circle
                    cx="40"
                    cy="40"
                    r="32"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                    className="text-gray-200"
                  />
                  <circle
                    cx="40"
                    cy="40"
                    r="32"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                    strokeDasharray={2 * Math.PI * 32}
                    strokeDashoffset={2 * Math.PI * 32 * (1 - analytics.system_metrics.memory_usage / 100)}
                    className="text-green-600"
                    transform="rotate(-90 40 40)"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-sm font-semibold text-gray-900">{analytics.system_metrics.memory_usage}%</span>
                </div>
              </div>
              <p className="mt-2 text-sm font-medium text-gray-900">Memory Usage</p>
              <div className="flex items-center justify-center mt-1">
                <Database className="h-4 w-4 text-gray-400 mr-1" />
                <span className="text-xs text-gray-500">16GB RAM</span>
              </div>
            </div>
            <div className="text-center">
              <div className="relative">
                <svg className="w-20 h-20 mx-auto">
                  <circle
                    cx="40"
                    cy="40"
                    r="32"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                    className="text-gray-200"
                  />
                  <circle
                    cx="40"
                    cy="40"
                    r="32"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                    strokeDasharray={2 * Math.PI * 32}
                    strokeDashoffset={2 * Math.PI * 32 * (1 - analytics.system_metrics.disk_usage / 100)}
                    className="text-purple-600"
                    transform="rotate(-90 40 40)"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-sm font-semibold text-gray-900">{analytics.system_metrics.disk_usage}%</span>
                </div>
              </div>
              <p className="mt-2 text-sm font-medium text-gray-900">Disk Usage</p>
              <div className="flex items-center justify-center mt-1">
                <Database className="h-4 w-4 text-gray-400 mr-1" />
                <span className="text-xs text-gray-500">1TB SSD</span>
              </div>
            </div>
            <div className="text-center">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="text-3xl font-bold text-blue-600">{analytics.system_metrics.active_connections}</div>
                <p className="mt-2 text-sm font-medium text-gray-900">Active Connections</p>
                <div className="flex items-center justify-center mt-1">
                  <Activity className="h-4 w-4 text-gray-400 mr-1" />
                  <span className="text-xs text-gray-500">Real-time</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* API Endpoints Performance */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-medium text-gray-900">Top API Endpoints</h2>
          <button className="text-blue-600 hover:text-blue-900 text-sm font-medium">
            View All
          </button>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Endpoint
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Requests
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Response Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Errors
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Success Rate
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {analytics.api_endpoints.map((endpoint, index) => {
                const successRate = ((endpoint.requests - endpoint.error_count) / endpoint.requests * 100);
                return (
                  <tr key={endpoint.endpoint} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900 font-mono">
                        {endpoint.endpoint}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatNumber(endpoint.requests)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        endpoint.avg_response_time > 200 ? 'bg-red-100 text-red-800' :
                        endpoint.avg_response_time > 100 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {endpoint.avg_response_time}ms
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {endpoint.error_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-full bg-gray-200 rounded-full h-2 mr-2">
                          <div
                            className="bg-green-600 h-2 rounded-full"
                            style={{ width: `${successRate}%` }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-600 min-w-max">
                          {successRate.toFixed(1)}%
                        </span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}