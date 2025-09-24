'use client';

import { useState, useEffect } from 'react';
import {
  User,
  Mail,
  Lock,
  Bell,
  Shield,
  Globe,
  Moon,
  Sun,
  Monitor,
  Palette,
  Database,
  Key,
  AlertCircle,
  CheckCircle,
  Save
} from 'lucide-react';

interface SettingSection {
  id: string;
  title: string;
  description: string;
  icon: React.ElementType;
}

const sections: SettingSection[] = [
  { id: 'profile', title: 'Profile', description: 'Manage your personal information', icon: User },
  { id: 'security', title: 'Security', description: 'Password and authentication settings', icon: Shield },
  { id: 'notifications', title: 'Notifications', description: 'Email and system notifications', icon: Bell },
  { id: 'appearance', title: 'Appearance', description: 'Theme and display preferences', icon: Palette },
  { id: 'api', title: 'API Keys', description: 'Manage API access tokens', icon: Key },
  { id: 'data', title: 'Data & Privacy', description: 'Data export and privacy settings', icon: Database },
];

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState('profile');
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('dark');
  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    updates: true,
    security: true,
  });
  const [profile, setProfile] = useState({
    full_name: '',
    email: '',
    username: '',
    phone: '',
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    // Load user profile
    loadUserProfile();
  }, []);

  const loadUserProfile = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;

      const response = await fetch('http://localhost:8000/api/v1/auth/me', {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        setProfile({
          full_name: data.full_name || '',
          email: data.email || '',
          username: data.username || '',
          phone: data.phone || '',
        });
      }
    } catch (error) {
      console.error('Failed to load profile:', error);
    }
  };

  const handleSaveProfile = async () => {
    setLoading(true);
    setMessage(null);

    // Simulate save operation
    setTimeout(() => {
      setMessage({ type: 'success', text: 'Profile settings saved successfully!' });
      setLoading(false);
      setTimeout(() => setMessage(null), 3000);
    }, 1000);
  };

  const handlePasswordChange = async () => {
    setLoading(true);
    setMessage(null);

    // Simulate password change
    setTimeout(() => {
      setMessage({ type: 'success', text: 'Password updated successfully!' });
      setLoading(false);
      setTimeout(() => setMessage(null), 3000);
    }, 1000);
  };

  const renderContent = () => {
    switch (activeSection) {
      case 'profile':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-slate-100 mb-4">Profile Information</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Full Name</label>
                  <input
                    type="text"
                    value={profile.full_name}
                    onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Username</label>
                  <input
                    type="text"
                    value={profile.username}
                    onChange={(e) => setProfile({ ...profile, username: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Email Address</label>
                  <input
                    type="email"
                    value={profile.email}
                    onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Phone Number</label>
                  <input
                    type="tel"
                    value={profile.phone}
                    onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>
                <button
                  onClick={handleSaveProfile}
                  disabled={loading}
                  className="px-4 py-2 bg-sky-500 hover:bg-sky-600 disabled:bg-slate-700 text-white rounded-lg transition-colors flex items-center gap-2"
                >
                  <Save className="h-4 w-4" />
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          </div>
        );

      case 'security':
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-medium text-slate-100 mb-4">Change Password</h3>
              <div className="space-y-4 max-w-md">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Current Password</label>
                  <input
                    type="password"
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">New Password</label>
                  <input
                    type="password"
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Confirm New Password</label>
                  <input
                    type="password"
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-sky-500"
                  />
                </div>
                <button
                  onClick={handlePasswordChange}
                  disabled={loading}
                  className="px-4 py-2 bg-sky-500 hover:bg-sky-600 disabled:bg-slate-700 text-white rounded-lg transition-colors"
                >
                  {loading ? 'Updating...' : 'Update Password'}
                </button>
              </div>
            </div>

            <div className="pt-6 border-t border-slate-800">
              <h3 className="text-lg font-medium text-slate-100 mb-4">Two-Factor Authentication</h3>
              <p className="text-sm text-slate-400 mb-4">Add an extra layer of security to your account</p>
              <button className="px-4 py-2 border border-slate-700 text-slate-300 rounded-lg hover:bg-slate-800 transition-colors">
                Enable 2FA
              </button>
            </div>
          </div>
        );

      case 'notifications':
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-slate-100 mb-4">Notification Preferences</h3>
            <div className="space-y-4">
              <label className="flex items-center justify-between p-4 bg-slate-900/50 border border-slate-800 rounded-lg cursor-pointer hover:bg-slate-800/50">
                <div className="flex items-center gap-3">
                  <Mail className="h-5 w-5 text-slate-400" />
                  <div>
                    <div className="text-sm font-medium text-slate-200">Email Notifications</div>
                    <div className="text-xs text-slate-400">Receive updates via email</div>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.email}
                  onChange={(e) => setNotifications({ ...notifications, email: e.target.checked })}
                  className="h-4 w-4 rounded border-slate-700 bg-slate-800 text-sky-500"
                />
              </label>

              <label className="flex items-center justify-between p-4 bg-slate-900/50 border border-slate-800 rounded-lg cursor-pointer hover:bg-slate-800/50">
                <div className="flex items-center gap-3">
                  <Bell className="h-5 w-5 text-slate-400" />
                  <div>
                    <div className="text-sm font-medium text-slate-200">Push Notifications</div>
                    <div className="text-xs text-slate-400">Browser push notifications</div>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.push}
                  onChange={(e) => setNotifications({ ...notifications, push: e.target.checked })}
                  className="h-4 w-4 rounded border-slate-700 bg-slate-800 text-sky-500"
                />
              </label>

              <label className="flex items-center justify-between p-4 bg-slate-900/50 border border-slate-800 rounded-lg cursor-pointer hover:bg-slate-800/50">
                <div className="flex items-center gap-3">
                  <Globe className="h-5 w-5 text-slate-400" />
                  <div>
                    <div className="text-sm font-medium text-slate-200">Product Updates</div>
                    <div className="text-xs text-slate-400">New features and improvements</div>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.updates}
                  onChange={(e) => setNotifications({ ...notifications, updates: e.target.checked })}
                  className="h-4 w-4 rounded border-slate-700 bg-slate-800 text-sky-500"
                />
              </label>

              <label className="flex items-center justify-between p-4 bg-slate-900/50 border border-slate-800 rounded-lg cursor-pointer hover:bg-slate-800/50">
                <div className="flex items-center gap-3">
                  <Shield className="h-5 w-5 text-slate-400" />
                  <div>
                    <div className="text-sm font-medium text-slate-200">Security Alerts</div>
                    <div className="text-xs text-slate-400">Important security notifications</div>
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={notifications.security}
                  onChange={(e) => setNotifications({ ...notifications, security: e.target.checked })}
                  className="h-4 w-4 rounded border-slate-700 bg-slate-800 text-sky-500"
                />
              </label>
            </div>
          </div>
        );

      case 'appearance':
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-slate-100 mb-4">Appearance Settings</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-3">Theme</label>
                <div className="grid grid-cols-3 gap-3 max-w-md">
                  <button
                    onClick={() => setTheme('light')}
                    className={`p-4 border rounded-lg flex flex-col items-center gap-2 transition-colors ${
                      theme === 'light'
                        ? 'border-sky-500 bg-sky-500/10'
                        : 'border-slate-700 hover:bg-slate-800'
                    }`}
                  >
                    <Sun className="h-5 w-5 text-slate-400" />
                    <span className="text-sm text-slate-300">Light</span>
                  </button>
                  <button
                    onClick={() => setTheme('dark')}
                    className={`p-4 border rounded-lg flex flex-col items-center gap-2 transition-colors ${
                      theme === 'dark'
                        ? 'border-sky-500 bg-sky-500/10'
                        : 'border-slate-700 hover:bg-slate-800'
                    }`}
                  >
                    <Moon className="h-5 w-5 text-slate-400" />
                    <span className="text-sm text-slate-300">Dark</span>
                  </button>
                  <button
                    onClick={() => setTheme('system')}
                    className={`p-4 border rounded-lg flex flex-col items-center gap-2 transition-colors ${
                      theme === 'system'
                        ? 'border-sky-500 bg-sky-500/10'
                        : 'border-slate-700 hover:bg-slate-800'
                    }`}
                  >
                    <Monitor className="h-5 w-5 text-slate-400" />
                    <span className="text-sm text-slate-300">System</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        );

      case 'api':
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-slate-100 mb-4">API Keys</h3>
            <p className="text-sm text-slate-400 mb-4">Manage your API keys for programmatic access</p>

            <div className="space-y-3">
              <div className="p-4 bg-slate-900/50 border border-slate-800 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium text-slate-200">Production API Key</div>
                  <span className="text-xs px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded-full">Active</span>
                </div>
                <div className="font-mono text-xs text-slate-400">sk_live_...4a2b</div>
                <div className="text-xs text-slate-500 mt-2">Created: Jan 15, 2024</div>
              </div>

              <div className="p-4 bg-slate-900/50 border border-slate-800 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-medium text-slate-200">Development API Key</div>
                  <span className="text-xs px-2 py-1 bg-amber-500/20 text-amber-400 rounded-full">Test</span>
                </div>
                <div className="font-mono text-xs text-slate-400">sk_test_...8f3c</div>
                <div className="text-xs text-slate-500 mt-2">Created: Jan 10, 2024</div>
              </div>
            </div>

            <button className="px-4 py-2 bg-sky-500 hover:bg-sky-600 text-white rounded-lg transition-colors">
              Generate New API Key
            </button>
          </div>
        );

      case 'data':
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-medium text-slate-100 mb-4">Data & Privacy</h3>

            <div className="space-y-4">
              <div className="p-4 bg-slate-900/50 border border-slate-800 rounded-lg">
                <h4 className="text-sm font-medium text-slate-200 mb-2">Export Your Data</h4>
                <p className="text-xs text-slate-400 mb-3">Download all your data in JSON format</p>
                <button className="px-3 py-1.5 text-sm border border-slate-700 text-slate-300 rounded-lg hover:bg-slate-800 transition-colors">
                  Request Export
                </button>
              </div>

              <div className="p-4 bg-slate-900/50 border border-slate-800 rounded-lg">
                <h4 className="text-sm font-medium text-slate-200 mb-2">Delete Account</h4>
                <p className="text-xs text-slate-400 mb-3">Permanently delete your account and all data</p>
                <button className="px-3 py-1.5 text-sm border border-rose-500/50 text-rose-400 rounded-lg hover:bg-rose-500/10 transition-colors">
                  Delete Account
                </button>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="p-6">
      <div className="max-w-6xl mx-auto">
        {/* Page Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-slate-100">Settings</h1>
          <p className="text-slate-400 mt-1">Manage your account and application preferences</p>
        </div>

        {/* Success/Error Messages */}
        {message && (
          <div className={`mb-6 p-4 rounded-lg flex items-center gap-2 ${
            message.type === 'success'
              ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
              : 'bg-rose-500/10 border border-rose-500/20 text-rose-400'
          }`}>
            {message.type === 'success' ? (
              <CheckCircle className="h-4 w-4 flex-shrink-0" />
            ) : (
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
            )}
            <span className="text-sm">{message.text}</span>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar Navigation */}
          <div className="lg:col-span-1">
            <nav className="space-y-1">
              {sections.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    activeSection === section.id
                      ? 'bg-sky-500/10 text-sky-400'
                      : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                  }`}
                >
                  <section.icon className="h-5 w-5 flex-shrink-0" />
                  <div className="text-left">
                    <div>{section.title}</div>
                    <div className="text-xs text-slate-500">{section.description}</div>
                  </div>
                </button>
              ))}
            </nav>
          </div>

          {/* Content Area */}
          <div className="lg:col-span-3 bg-slate-900/50 border border-slate-800 rounded-lg p-6">
            {renderContent()}
          </div>
        </div>
      </div>
    </div>
  );
}