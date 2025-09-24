'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Home,
  Settings,
  Users,
  UserCheck,
  Shield,
  Database,
  Activity,
  Mail,
  Search,
  FileText,
  ToggleLeft,
  Menu,
  X,
  LogOut,
  User,
  ChevronDown,
  Key,
  Webhook
} from 'lucide-react';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
}

const navigation: NavItem[] = [
  { name: 'Overview', href: '/dashboard', icon: Home },
  { name: 'Customers', href: '/dashboard/customers', icon: UserCheck },
  { name: 'Users', href: '/dashboard/users', icon: Users },
  { name: 'API Keys', href: '/dashboard/api-keys', icon: Key },
  { name: 'Webhooks', href: '/dashboard/webhooks', icon: Webhook },
  { name: 'Secrets', href: '/dashboard/secrets', icon: Shield },
  { name: 'Analytics', href: '/dashboard/analytics', icon: Activity },
  { name: 'Files', href: '/dashboard/files', icon: Database },
  { name: 'Communications', href: '/dashboard/communications', icon: Mail },
  { name: 'Search', href: '/dashboard/search', icon: Search },
  { name: 'Feature Flags', href: '/dashboard/feature-flags', icon: ToggleLeft },
  { name: 'Logs', href: '/dashboard/logs', icon: FileText },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [user, setUser] = useState<any>(null);
  const pathname = usePathname();

  // Fetch current user
  useEffect(() => {
    fetchCurrentUser();
  }, []);

  const fetchCurrentUser = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        window.location.href = '/login';
        return;
      }

      const response = await fetch('http://localhost:8000/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else if (response.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
    } catch (error) {
      console.error('Failed to fetch user:', error);
    }
  };

  const handleLogout = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        await fetch('http://localhost:8000/api/v1/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
      }
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    } catch (error) {
      console.error('Logout error:', error);
      // Still redirect even if logout fails
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Top Navigation Bar */}
      <div className="fixed top-0 left-0 right-0 z-50 bg-slate-900 border-b border-slate-800">
        <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="flex items-center">
            <button
              type="button"
              className="lg:hidden -m-2.5 inline-flex items-center justify-center rounded-md p-2.5 text-slate-400 hover:bg-slate-800"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              <Menu className="h-6 w-6" />
            </button>
            <div className="flex items-center ml-4 lg:ml-0">
              <div className="text-xl font-semibold text-white">DotMac Platform</div>
            </div>
          </div>

          {/* Right side - User menu */}
          <div className="flex items-center gap-4">
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800 transition-colors"
              >
                <User className="h-5 w-5" />
                <span className="hidden sm:block">{user?.username || 'User'}</span>
                <ChevronDown className="h-4 w-4" />
              </button>

              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-56 rounded-md bg-slate-800 shadow-lg ring-1 ring-black ring-opacity-5">
                  <div className="py-1">
                    <div className="px-4 py-2 text-sm text-slate-400">
                      <div className="font-semibold text-slate-200">{user?.full_name || user?.username}</div>
                      <div className="text-xs">{user?.email}</div>
                      <div className="text-xs mt-1">Role: {user?.roles?.join(', ') || 'User'}</div>
                    </div>
                    <hr className="my-1 border-slate-700" />
                    <Link
                      href="/dashboard/profile"
                      className="block px-4 py-2 text-sm text-slate-300 hover:bg-slate-700"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      Profile Settings
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="block w-full text-left px-4 py-2 text-sm text-slate-300 hover:bg-slate-700"
                    >
                      <div className="flex items-center gap-2">
                        <LogOut className="h-4 w-4" />
                        Sign Out
                      </div>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 z-40 w-64 bg-slate-900 pt-16 transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full'
      }`}>
        {/* Mobile close button */}
        <div className="lg:hidden absolute top-20 right-4">
          <button
            onClick={() => setSidebarOpen(false)}
            className="rounded-md p-2 text-slate-400 hover:bg-slate-800"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation items */}
        <nav className="mt-8 px-4">
          <ul className="space-y-1">
            {navigation.map((item) => {
              const isActive = pathname === item.href ||
                (item.href !== '/dashboard' && pathname.startsWith(item.href));
              return (
                <li key={item.name}>
                  <Link
                    href={item.href}
                    className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-sky-500/10 text-sky-400'
                        : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                    }`}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <item.icon className="h-5 w-5 flex-shrink-0" />
                    <span>{item.name}</span>
                    {item.badge && (
                      <span className="ml-auto bg-sky-500/20 text-sky-400 text-xs px-2 py-0.5 rounded-full">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Bottom section with version info */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-800">
          <div className="text-xs text-slate-500">
            <div>Platform Version: 1.0.0</div>
            <div>Environment: Development</div>
          </div>
        </div>
      </div>

      {/* Main content area */}
      <div className="lg:pl-64 pt-16">
        <main className="min-h-screen">
          {children}
        </main>
      </div>

      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
    </div>
  );
}