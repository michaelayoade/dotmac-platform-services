'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { getCurrentUser, logout as logoutUser } from '@/lib/auth';
import { platformConfig } from '@/lib/config';
import { logger } from '@/lib/utils/logger';

interface User {
  id: string;
  email: string;
  name?: string;
  roles?: string[];
}

interface HealthCheck {
  status: string;
  service: string;
  version: string;
  checks?: Record<string, string>;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [health, setHealth] = useState<HealthCheck | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isMounted = true;

    const loadUser = async () => {
      try {
        const currentUser = await getCurrentUser();
        if (!isMounted) return;
        setUser(currentUser);
      } catch (err) {
        logger.error('Failed to fetch user', err instanceof Error ? err : new Error(String(err)));
        if (!isMounted) return;
        router.replace('/login');
      }
    };

    const loadHealth = async () => {
      try {
        const baseUrl = platformConfig.apiBaseUrl || '';
        const healthPath = `${baseUrl}/health`;
        const response = await fetch(healthPath);
        if (!isMounted) return;
        if (!response.ok) {
          logger.error('Failed to fetch health status', new Error(`HTTP ${response.status}`));
          return;
        }
        const data = await response.json();
        setHealth(data);
      } catch (error) {
        if (!isMounted) return;
        logger.error('Failed to fetch health status', error instanceof Error ? error : new Error(String(error)));
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadUser();
    loadHealth();

    return () => {
      isMounted = false;
    };
  }, [router]);

  const handleLogout = async () => {
    try {
      await logoutUser();
    } finally {
      router.push('/login');
    }
  };

  const handleProfileClick = async () => {
    // Trigger /api/v1/auth/me API call for testing
    try {
      await getCurrentUser();
    } catch (err) {
      logger.error('Failed to fetch user profile', err instanceof Error ? err : new Error(String(err)));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="text-slate-400">Loading...</div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <header className="bg-slate-900/50 backdrop-blur border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-xl font-semibold">DotMac Platform Dashboard</h1>
            <p className="text-sm text-slate-400 mt-1">
              Welcome back, {user?.email || 'User'}
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleProfileClick}
              data-testid="user-profile-button"
              className="px-4 py-2 text-sm bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            >
              Profile
            </button>
            <button
              onClick={handleLogout}
              data-testid="logout-button"
              className="px-4 py-2 text-sm bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-12" data-testid="dashboard-content">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {/* User Info Card */}
          <div className="bg-slate-900/50 backdrop-blur border border-slate-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4 text-sky-400">User Profile</h2>
            <div className="space-y-2 text-sm">
              <div>
                <span className="text-slate-400">Email:</span>
                <span className="ml-2">{user?.email}</span>
              </div>
              <div>
                <span className="text-slate-400">User ID:</span>
                <span className="ml-2 font-mono text-xs">{user?.id}</span>
              </div>
              {user?.roles && user.roles.length > 0 && (
                <div>
                  <span className="text-slate-400">Roles:</span>
                  <span className="ml-2">{user.roles.join(', ')}</span>
                </div>
              )}
            </div>
          </div>

          {/* API Health Card */}
          <div className="bg-slate-900/50 backdrop-blur border border-slate-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4 text-emerald-400">API Status</h2>
            {health ? (
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-emerald-400 rounded-full"></span>
                  <span>{health.status}</span>
                </div>
                <div>
                  <span className="text-slate-400">Service:</span>
                  <span className="ml-2">{health.service}</span>
                </div>
                {health.version && (
                  <div>
                    <span className="text-slate-400">Version:</span>
                    <span className="ml-2">{health.version}</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-slate-500 text-sm">Unable to fetch status</div>
            )}
          </div>

          {/* Quick Actions Card */}
          <div className="bg-slate-900/50 backdrop-blur border border-slate-800 rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4 text-purple-400">Quick Actions</h2>
            <div className="space-y-3">
              <Link
                href="/dashboard/customers"
                className="block px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm text-center transition-colors"
              >
                Manage Customers
              </Link>
              <Link
                href="/dashboard/billing"
                className="block px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm text-center transition-colors"
              >
                Billing Overview
              </Link>
              <Link
                href="/dashboard/api-keys"
                className="block px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm text-center transition-colors"
              >
                Manage API Keys
              </Link>
            </div>
          </div>
        </div>

        {/* Services Grid */}
        <div className="mt-12">
          <h2 className="text-2xl font-semibold mb-6">Platform Services</h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[
              { name: 'Authentication', status: 'active', icon: '🔐' },
              { name: 'File Storage', status: 'active', icon: '📁' },
              { name: 'Secrets Manager', status: 'active', icon: '🔑' },
              { name: 'Analytics', status: 'active', icon: '📊' },
              { name: 'Communications', status: 'active', icon: '📧' },
              { name: 'Search', status: 'active', icon: '🔍' },
              { name: 'Data Transfer', status: 'active', icon: '🔄' },
              { name: 'API Gateway', status: 'active', icon: '🌐' },
            ].map((service) => (
              <div
                key={service.name}
                className="bg-slate-900/50 backdrop-blur border border-slate-800 rounded-lg p-4 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-2xl">{service.icon}</span>
                  <span className="w-2 h-2 bg-emerald-400 rounded-full"></span>
                </div>
                <h3 className="font-medium text-sm">{service.name}</h3>
                <p className="text-xs text-slate-400 mt-1">Status: {service.status}</p>
              </div>
            ))}
          </div>
        </div>

      </div>
    </main>
  );
}
