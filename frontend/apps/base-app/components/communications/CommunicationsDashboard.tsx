'use client';

import { useState, useEffect } from 'react';
import {
  Mail,
  MessageSquare,
  Send,
  CheckCircle,
  XCircle,
  Clock,
  Users,
  BarChart,
  AlertCircle,
  Webhook,
  RefreshCw,
  X,
  Inbox
} from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import { useToast } from '@/components/ui/use-toast';
import { logger } from '@/lib/utils/logger';

// Migrated from sonner to useToast hook
// Note: toast options have changed:
// - sonner: toast.success('msg') -> useToast: toast({ title: 'Success', description: 'msg' })
// - sonner: toast.error('msg') -> useToast: toast({ title: 'Error', description: 'msg', variant: 'destructive' })
// - For complex options, refer to useToast documentation

interface EmailStats {
  sent: number;
  delivered: number;
  failed: number;
  pending: number;
}

interface RecentActivity {
  id: string;
  type: 'email' | 'webhook' | 'sms';
  recipient: string;
  subject?: string;
  status: 'sent' | 'delivered' | 'failed' | 'pending';
  timestamp: string;
}

export function CommunicationsDashboard() {
  const { toast } = useToast();

  const [stats, setStats] = useState<EmailStats>({
    sent: 0,
    delivered: 0,
    failed: 0,
    pending: 0
  });
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showComposeModal, setShowComposeModal] = useState(false);
  const [sending, setSending] = useState(false);
  const [messageForm, setMessageForm] = useState({
    type: 'email',
    recipient: '',
    subject: '',
    message: ''
  });

  useEffect(() => {
    fetchCommunicationData();
  }, []);

  const fetchCommunicationData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch stats from API
      const statsResponse = await apiClient.get<EmailStats>('/api/v1/communications/stats');

      if (statsResponse.success && statsResponse.data) {
        setStats(statsResponse.data);
      } else {
        logger.error('Failed to fetch stats', new Error(statsResponse.error?.message || 'Failed to fetch stats'), { error: statsResponse.error });
      }

      // Fetch recent activity from API
      const activityResponse = await apiClient.get<RecentActivity[]>('/api/v1/communications/activity?limit=20');

      if (activityResponse.success && activityResponse.data) {
        setRecentActivity(activityResponse.data);
      } else {
        logger.error('Failed to fetch activity', new Error(activityResponse.error?.message || 'Failed to fetch activity'), { error: activityResponse.error });
      }
    } catch (err) {
      logger.error('Failed to fetch communication data', err instanceof Error ? err : new Error(String(err)));
      setError('Failed to load communication data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'delivered':
        return <CheckCircle className="h-4 w-4 text-green-400" />;
      case 'sent':
        return <Send className="h-4 w-4 text-sky-400" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-400" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-400" />;
      default:
        return <AlertCircle className="h-4 w-4 text-slate-400" />;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'email':
        return <Mail className="h-4 w-4 text-slate-400" />;
      case 'webhook':
        return <Webhook className="h-4 w-4 text-slate-400" />;
      case 'sms':
        return <MessageSquare className="h-4 w-4 text-slate-400" />;
      default:
        return <AlertCircle className="h-4 w-4 text-slate-400" />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

    if (diffHours < 1) {
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      return `${diffMinutes} minutes ago`;
    } else if (diffHours < 24) {
      return `${diffHours} hours ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-slate-400">Loading communications data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-red-400">{error}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-50">Communications</h1>
        <button
          onClick={() => setShowComposeModal(true)}
          className="px-4 py-2 bg-sky-500 hover:bg-sky-600 text-white rounded-lg transition-colors flex items-center gap-2"
        >
          <Send className="h-4 w-4" />
          Send Message
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">Total Sent</p>
              <p className="text-2xl font-bold text-slate-50 mt-2">{stats.sent.toLocaleString()}</p>
            </div>
            <Send className="h-8 w-8 text-sky-400" />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">Delivered</p>
              <p className="text-2xl font-bold text-slate-50 mt-2">{stats.delivered.toLocaleString()}</p>
            </div>
            <CheckCircle className="h-8 w-8 text-green-400" />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">Failed</p>
              <p className="text-2xl font-bold text-slate-50 mt-2">{stats.failed.toLocaleString()}</p>
            </div>
            <XCircle className="h-8 w-8 text-red-400" />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">Pending</p>
              <p className="text-2xl font-bold text-slate-50 mt-2">{stats.pending.toLocaleString()}</p>
            </div>
            <Clock className="h-8 w-8 text-yellow-400" />
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg">
        <div className="p-6 border-b border-slate-800">
          <h2 className="text-lg font-semibold text-slate-50">Recent Activity</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="text-left px-6 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Type</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Recipient</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Subject</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Status</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-slate-400 uppercase tracking-wider">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {recentActivity.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center">
                      <Inbox className="h-12 w-12 text-slate-600 mb-4" />
                      <p className="text-slate-400 text-lg font-medium">No recent activity</p>
                      <p className="text-slate-500 text-sm mt-2">Communications will appear here once sent</p>
                    </div>
                  </td>
                </tr>
              ) : recentActivity.map((activity) => (
                <tr key={activity.id} className="hover:bg-slate-800/50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      {getTypeIcon(activity.type)}
                      <span className="text-sm text-slate-300 capitalize">{activity.type}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-slate-300">{activity.recipient}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm text-slate-300">{activity.subject || '-'}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(activity.status)}
                      <span className="text-sm text-slate-300 capitalize">{activity.status}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-slate-400">{formatTimestamp(activity.timestamp)}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button className="bg-slate-900 border border-slate-800 rounded-lg p-6 hover:bg-slate-800 transition-colors text-left">
          <Mail className="h-8 w-8 text-sky-400 mb-4" />
          <h3 className="text-lg font-semibold text-slate-50 mb-2">Email Templates</h3>
          <p className="text-sm text-slate-400">Manage and create email templates</p>
        </button>

        <button className="bg-slate-900 border border-slate-800 rounded-lg p-6 hover:bg-slate-800 transition-colors text-left">
          <Users className="h-8 w-8 text-green-400 mb-4" />
          <h3 className="text-lg font-semibold text-slate-50 mb-2">Recipient Lists</h3>
          <p className="text-sm text-slate-400">Manage recipient groups and lists</p>
        </button>

        <button className="bg-slate-900 border border-slate-800 rounded-lg p-6 hover:bg-slate-800 transition-colors text-left">
          <BarChart className="h-8 w-8 text-purple-400 mb-4" />
          <h3 className="text-lg font-semibold text-slate-50 mb-2">Analytics</h3>
          <p className="text-sm text-slate-400">View detailed communication analytics</p>
        </button>
      </div>

      {/* Compose Message Modal */}
      {showComposeModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-slate-800">
              <h2 className="text-xl font-semibold text-slate-50">Compose Message</h2>
              <button
                onClick={() => setShowComposeModal(false)}
                className="text-slate-400 hover:text-slate-300 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-4 overflow-y-auto max-h-[calc(90vh-200px)]">
              {/* Message Type */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Type</label>
                <select
                  value={messageForm.type}
                  onChange={(e) => setMessageForm({ ...messageForm, type: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
                >
                  <option value="email">Email</option>
                  <option value="sms">SMS</option>
                  <option value="webhook">Webhook</option>
                </select>
              </div>

              {/* Recipient */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  {messageForm.type === 'email' ? 'Email Address' :
                   messageForm.type === 'sms' ? 'Phone Number' :
                   'Webhook URL'}
                </label>
                <input
                  type={messageForm.type === 'email' ? 'email' : 'text'}
                  value={messageForm.recipient}
                  onChange={(e) => setMessageForm({ ...messageForm, recipient: e.target.value })}
                  placeholder={
                    messageForm.type === 'email' ? 'recipient@example.com' :
                    messageForm.type === 'sms' ? '+1234567890' :
                    'https://api.example.com/webhook'
                  }
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
                />
              </div>

              {/* Subject (for email only) */}
              {messageForm.type === 'email' && (
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Subject</label>
                  <input
                    type="text"
                    value={messageForm.subject}
                    onChange={(e) => setMessageForm({ ...messageForm, subject: e.target.value })}
                    placeholder="Enter subject"
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
                  />
                </div>
              )}

              {/* Message */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  {messageForm.type === 'webhook' ? 'Payload (JSON)' : 'Message'}
                </label>
                <textarea
                  value={messageForm.message}
                  onChange={(e) => setMessageForm({ ...messageForm, message: e.target.value })}
                  placeholder={
                    messageForm.type === 'webhook' ?
                    '{\n  "event": "notification",\n  "data": {}\n}' :
                    'Enter your message here...'
                  }
                  rows={8}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent font-mono"
                />
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-3 p-6 border-t border-slate-800">
              <button
                onClick={() => setShowComposeModal(false)}
                className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
                disabled={sending}
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  if (!messageForm.recipient) {
                    toast({ title: 'Error', description: 'Please enter a recipient', variant: 'destructive' });
                    return;
                  }
                  if (messageForm.type === 'email' && !messageForm.subject) {
                    toast({ title: 'Error', description: 'Please enter a subject', variant: 'destructive' });
                    return;
                  }
                  if (!messageForm.message) {
                    toast({ title: 'Error', description: 'Please enter a message', variant: 'destructive' });
                    return;
                  }

                  setSending(true);
                  try {
                    // Simulate API call
                    await new Promise(resolve => setTimeout(resolve, 1500));

                    // Add to recent activity
                    const newActivity: RecentActivity = {
                      id: Date.now().toString(),
                      type: messageForm.type as any,
                      recipient: messageForm.recipient,
                      subject: messageForm.subject,
                      status: 'sent',
                      timestamp: new Date().toISOString()
                    };

                    setRecentActivity([newActivity, ...recentActivity]);
                    setStats({ ...stats, sent: stats.sent + 1 });

                    toast({ title: 'Success', description: `${messageForm.type === 'email' ? 'Email' : messageForm.type === 'sms' ? 'SMS' : 'Webhook'} sent successfully` });
                    setShowComposeModal(false);
                    setMessageForm({ type: 'email', recipient: '', subject: '', message: '' });
                  } catch (error) {
                    toast({ title: 'Error', description: 'Failed to send message. Please try again.', variant: 'destructive' });
                  } finally {
                    setSending(false);
                  }
                }}
                disabled={sending}
                className="px-4 py-2 bg-sky-500 hover:bg-sky-600 disabled:bg-sky-500/50 text-white rounded-lg transition-colors flex items-center gap-2"
              >
                {sending ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    Sending...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                    Send Message
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}