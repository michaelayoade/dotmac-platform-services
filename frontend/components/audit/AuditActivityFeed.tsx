import React, { useEffect, useState, useCallback } from 'react';
import { format } from 'date-fns';
import {
  Activity,
  AlertCircle,
  CheckCircle,
  Info,
  Lock,
  User,
  FileText,
  Database,
  Mail,
  Globe,
  Clock,
  XCircle
} from 'lucide-react';

// Types
interface AuditActivity {
  id: string;
  activity_type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  user_id: string;
  timestamp: string;
  action: string;
  description: string;
  resource_type?: string;
  resource_id?: string;
  details?: Record<string, any>;
  ip_address?: string;
  user_agent?: string;
}

interface AuditActivityFeedProps {
  userId?: string;
  limit?: number;
  days?: number;
  autoRefresh?: boolean;
  refreshInterval?: number;
  onActivityClick?: (activity: AuditActivity) => void;
}

// Utility functions
const getActivityIcon = (activityType: string) => {
  const iconMap: Record<string, React.ElementType> = {
    'user.login': User,
    'user.logout': User,
    'user.created': User,
    'user.updated': User,
    'user.deleted': User,
    'secret.created': Lock,
    'secret.accessed': Lock,
    'secret.updated': Lock,
    'secret.deleted': Lock,
    'file.uploaded': FileText,
    'file.downloaded': FileText,
    'file.deleted': FileText,
    'api.request': Globe,
    'api.error': AlertCircle,
    'system.startup': Activity,
    'system.shutdown': Activity,
  };
  return iconMap[activityType] || Activity;
};

const getSeverityColor = (severity: string) => {
  const colorMap: Record<string, string> = {
    LOW: 'text-green-600 bg-green-50',
    MEDIUM: 'text-yellow-600 bg-yellow-50',
    HIGH: 'text-orange-600 bg-orange-50',
    CRITICAL: 'text-red-600 bg-red-50',
  };
  return colorMap[severity] || 'text-gray-600 bg-gray-50';
};

const getSeverityIcon = (severity: string) => {
  switch (severity) {
    case 'LOW':
      return CheckCircle;
    case 'MEDIUM':
      return Info;
    case 'HIGH':
      return AlertCircle;
    case 'CRITICAL':
      return XCircle;
    default:
      return Info;
  }
};

// Activity Item Component
const ActivityItem: React.FC<{
  activity: AuditActivity;
  onClick?: (activity: AuditActivity) => void;
}> = ({ activity, onClick }) => {
  const Icon = getActivityIcon(activity.activity_type);
  const SeverityIcon = getSeverityIcon(activity.severity);
  const severityColors = getSeverityColor(activity.severity);

  return (
    <div
      className="flex items-start space-x-3 p-4 hover:bg-gray-50 transition-colors cursor-pointer border-b border-gray-100"
      onClick={() => onClick?.(activity)}
    >
      {/* Activity Icon */}
      <div className="flex-shrink-0">
        <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
          <Icon className="w-5 h-5 text-blue-600" />
        </div>
      </div>

      {/* Activity Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-gray-900 truncate">
            {activity.description}
          </p>
          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${severityColors}`}>
            <SeverityIcon className="w-3 h-3 mr-1" />
            {activity.severity}
          </span>
        </div>

        <div className="mt-1 flex items-center space-x-4 text-xs text-gray-500">
          <span className="flex items-center">
            <Clock className="w-3 h-3 mr-1" />
            {format(new Date(activity.timestamp), 'MMM d, yyyy h:mm a')}
          </span>
          {activity.resource_type && (
            <span className="flex items-center">
              <Database className="w-3 h-3 mr-1" />
              {activity.resource_type}
            </span>
          )}
          {activity.ip_address && (
            <span className="flex items-center">
              <Globe className="w-3 h-3 mr-1" />
              {activity.ip_address}
            </span>
          )}
        </div>

        {/* Additional Details */}
        {activity.details && Object.keys(activity.details).length > 0 && (
          <div className="mt-2">
            <div className="inline-flex items-center space-x-2">
              {Object.entries(activity.details).slice(0, 3).map(([key, value]) => (
                <span
                  key={key}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-gray-100 text-gray-600"
                >
                  {key}: {String(value)}
                </span>
              ))}
              {Object.keys(activity.details).length > 3 && (
                <span className="text-xs text-gray-500">
                  +{Object.keys(activity.details).length - 3} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Main Component
export const AuditActivityFeed: React.FC<AuditActivityFeedProps> = ({
  userId,
  limit = 20,
  days = 7,
  autoRefresh = false,
  refreshInterval = 30000,
  onActivityClick,
}) => {
  const [activities, setActivities] = useState<AuditActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchActivities = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        limit: limit.toString(),
        days: days.toString(),
      });

      if (userId) {
        params.append('user_id', userId);
      }

      const response = await fetch(`/api/v1/audit/activities/recent?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch activities');
      }

      const data = await response.json();
      setActivities(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, [userId, limit, days]);

  // Initial fetch
  useEffect(() => {
    fetchActivities();
  }, [fetchActivities]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(fetchActivities, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchActivities]);

  if (loading && activities.length === 0) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 rounded-lg">
        <div className="flex items-center">
          <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
          <p className="text-sm text-red-600">Error loading activities: {error}</p>
        </div>
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="p-8 text-center">
        <Activity className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-500">No recent activities found</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Recent Activities</h3>
          {autoRefresh && (
            <span className="text-xs text-gray-500">
              Auto-refreshing every {refreshInterval / 1000}s
            </span>
          )}
        </div>
      </div>

      <div className="divide-y divide-gray-200">
        {activities.map((activity) => (
          <ActivityItem
            key={activity.id}
            activity={activity}
            onClick={onActivityClick}
          />
        ))}
      </div>

      {activities.length >= limit && (
        <div className="p-4 text-center border-t border-gray-200">
          <button
            onClick={() => {/* Implement load more */}}
            className="text-sm text-blue-600 hover:text-blue-500 font-medium"
          >
            Load more activities
          </button>
        </div>
      )}
    </div>
  );
};

export default AuditActivityFeed;