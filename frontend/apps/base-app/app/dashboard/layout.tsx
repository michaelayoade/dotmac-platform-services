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
  ChevronRight,
  Key,
  Webhook,
  CreditCard,
  Repeat,
  Package,
  DollarSign,
  Server,
  Lock,
  BarChart3
} from 'lucide-react';
import { TenantSelector } from '@/components/tenant-selector';
import { apiClient } from '@/lib/api/client';
import { logger } from '@/lib/utils/logger';
import { Can } from '@/components/auth/PermissionGuard';
import { useRBAC } from '@/contexts/RBACContext';

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
  permission?: string;
}

interface NavSection {
  id: string;
  label: string;
  icon: React.ElementType;
  href: string;
  items?: NavItem[];
  permission?: string;
}

const sections: NavSection[] = [
  {
    id: 'overview',
    label: 'Overview',
    icon: Home,
    href: '/dashboard'
    // No permission required for overview
  },
  {
    id: 'operations',
    label: 'Operations',
    icon: Activity,
    href: '/dashboard/operations',
    items: [
      { name: 'Overview', href: '/dashboard/operations', icon: BarChart3 },
      { name: 'Customers', href: '/dashboard/operations/customers', icon: UserCheck, permission: 'customers.read' },
      { name: 'Communications', href: '/dashboard/operations/communications', icon: Mail, permission: 'communications.read' },
      { name: 'Files', href: '/dashboard/operations/files', icon: FileText },
    ],
  },
  {
    id: 'billing-revenue',
    label: 'Billing & Revenue',
    icon: DollarSign,
    href: '/dashboard/billing-revenue',
    permission: 'billing.read',
    items: [
      { name: 'Overview', href: '/dashboard/billing-revenue', icon: BarChart3, permission: 'billing.read' },
      { name: 'Invoices', href: '/dashboard/billing-revenue/invoices', icon: FileText, permission: 'billing.read' },
      { name: 'Subscriptions', href: '/dashboard/billing-revenue/subscriptions', icon: Repeat, permission: 'billing.read' },
      { name: 'Payments', href: '/dashboard/billing-revenue/payments', icon: CreditCard, permission: 'billing.read' },
      { name: 'Plans', href: '/dashboard/billing-revenue/plans', icon: Package, permission: 'billing.read' },
    ],
  },
  {
    id: 'security-access',
    label: 'Security & Access',
    icon: Shield,
    href: '/dashboard/security-access',
    items: [
      { name: 'Overview', href: '/dashboard/security-access', icon: BarChart3 },
      { name: 'API Keys', href: '/dashboard/security-access/api-keys', icon: Key, permission: 'settings.read' },
      { name: 'Secrets', href: '/dashboard/security-access/secrets', icon: Lock, permission: 'secrets.read' },
      { name: 'Roles', href: '/dashboard/security-access/roles', icon: Shield, permission: 'system.read' },
      { name: 'Role Management', href: '/dashboard/admin/roles', icon: Shield, permission: 'system.manage' },
      { name: 'Users', href: '/dashboard/security-access/users', icon: Users, permission: 'users.read' },
    ],
  },
  {
    id: 'infrastructure',
    label: 'Infrastructure',
    icon: Server,
    href: '/dashboard/infrastructure',
    permission: 'infrastructure.read',
    items: [
      { name: 'Overview', href: '/dashboard/infrastructure', icon: BarChart3, permission: 'infrastructure.read' },
      { name: 'Health', href: '/dashboard/infrastructure/health', icon: Activity, permission: 'infrastructure.read' },
      { name: 'Logs', href: '/dashboard/infrastructure/logs', icon: FileText, permission: 'infrastructure.read' },
      { name: 'Observability', href: '/dashboard/infrastructure/observability', icon: Search, permission: 'infrastructure.read' },
      { name: 'Feature Flags', href: '/dashboard/infrastructure/feature-flags', icon: ToggleLeft, permission: 'infrastructure.read' },
    ],
  },
  {
    id: 'admin',
    label: 'Administration',
    icon: Database,
    href: '/dashboard/admin',
    permission: 'system.manage',
    items: [
      { name: 'Overview', href: '/dashboard/admin', icon: BarChart3, permission: 'system.manage' },
      { name: 'Role Management', href: '/dashboard/admin/roles', icon: Shield, permission: 'system.manage' },
      { name: 'System Settings', href: '/dashboard/admin/system', icon: Settings, permission: 'system.manage' },
    ],
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: Settings,
    href: '/dashboard/settings',
    permission: 'settings.read',
    items: [
      { name: 'Profile', href: '/dashboard/settings/profile', icon: User },
      { name: 'Organization', href: '/dashboard/settings/organization', icon: Users, permission: 'settings.read' },
      { name: 'Billing', href: '/dashboard/settings/billing', icon: CreditCard, permission: 'billing.read' },
      { name: 'Notifications', href: '/dashboard/settings/notifications', icon: Mail, permission: 'settings.read' },
      { name: 'Integrations', href: '/dashboard/settings/integrations', icon: Package, permission: 'settings.read' },
    ],
  },
];

// Helper function to check if section should be visible
function checkSectionVisibility(section: NavSection, hasPermission: (permission: string) => boolean): boolean {
  // If section has explicit permission requirement, check it
  if (section.permission) {
    return hasPermission(section.permission);
  }

  // If section has no permission but has items, check if user has access to any item
  if (section.items && section.items.length > 0) {
    return section.items.some(item => !item.permission || hasPermission(item.permission));
  }

  // If no permission requirement and no items, show by default
  return true;
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [user, setUser] = useState<Record<string, unknown> | null>(null);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set());
  const pathname = usePathname();
  const { hasPermission } = useRBAC();

  // Type helper for user data
  const userData = user as { id?: string; username?: string; email?: string; full_name?: string; roles?: string[] } | null;

  // Filter sections based on permissions
  const visibleSections = sections.filter(section =>
    checkSectionVisibility(section, hasPermission)
  );

  // Toggle section expansion
  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
  };

  // Auto-expand active section
  useEffect(() => {
    visibleSections.forEach(section => {
      if (section.items?.some(item => pathname === item.href ||
         (item.href !== '/dashboard' && pathname.startsWith(item.href)))) {
        setExpandedSections(prev => new Set(prev).add(section.id));
      }
    });
  }, [pathname, visibleSections]);

  // Fetch current user
  useEffect(() => {
    fetchCurrentUser();
  }, []);

  const fetchCurrentUser = async () => {
    try {
      logger.debug('Dashboard: Fetching current user');
      const response = await apiClient.get('/api/v1/auth/me');

      if (response.success && response.data) {
        const userData = response.data as Record<string, unknown> & { id?: string };
        logger.info('Dashboard: User fetched successfully', { userId: userData.id });
        setUser(userData);
      } else {
        logger.warn('Dashboard: Failed to fetch user, redirecting to login', { response: response });
        // Token expired or invalid - redirect to login
        window.location.href = '/login';
      }
    } catch (error) {
      logger.error('Dashboard: Error fetching user', error instanceof Error ? error : new Error(String(error)));
      // On error, redirect to login
      window.location.href = '/login';
    }
  };

  const handleLogout = async () => {
    try {
      await apiClient.logout();
      // apiClient.logout() already redirects to login
    } catch (error) {
      logger.error('Logout error', error instanceof Error ? error : new Error(String(error)));
      // Still redirect even if logout fails
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

          {/* Right side - Tenant selector and User menu */}
          <div className="flex items-center gap-4">
            <TenantSelector />
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800 transition-colors"
              >
                <User className="h-5 w-5" />
                <span className="hidden sm:block">{userData?.username || 'User'}</span>
                <ChevronDown className="h-4 w-4" />
              </button>

              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-56 rounded-md bg-slate-800 shadow-lg ring-1 ring-black ring-opacity-5">
                  <div className="py-1">
                    <div className="px-4 py-2 text-sm text-slate-400">
                      <div className="font-semibold text-slate-200">{userData?.full_name || userData?.username}</div>
                      <div className="text-xs">{userData?.email}</div>
                      <div className="text-xs mt-1">Role: {userData?.roles?.join(', ') || 'User'}</div>
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
            {visibleSections.map((section) => {
              const isExpanded = expandedSections.has(section.id);
              const isSectionActive = pathname === section.href ||
                (section.href !== '/dashboard' && pathname.startsWith(section.href));
              const hasActiveChild = section.items?.some(item =>
                pathname === item.href ||
                (item.href !== '/dashboard' && pathname.startsWith(item.href))
              );

              return (
                <li key={section.id}>
                  <div>
                    {/* Section header */}
                    <div className="flex items-center">
                      <Link
                        href={section.href}
                        className={`flex-1 flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                          isSectionActive && !hasActiveChild
                            ? 'bg-sky-500/10 text-sky-400'
                            : hasActiveChild
                            ? 'text-slate-200'
                            : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                        }`}
                        onClick={() => setSidebarOpen(false)}
                      >
                        <section.icon className="h-5 w-5 flex-shrink-0" />
                        <span>{section.label}</span>
                      </Link>
                      {section.items && section.items.length > 0 && (
                        <button
                          onClick={() => toggleSection(section.id)}
                          className="p-1 mr-1 text-slate-400 hover:text-slate-200 transition-colors"
                        >
                          <ChevronRight className={`h-4 w-4 transform transition-transform ${
                            isExpanded ? 'rotate-90' : ''
                          }`} />
                        </button>
                      )}
                    </div>

                    {/* Section items */}
                    {section.items && isExpanded && (
                      <ul className="mt-1 ml-4 border-l border-slate-800 space-y-1">
                        {section.items.map((item) => {
                          const isItemActive = pathname === item.href ||
                            (item.href !== '/dashboard' && pathname.startsWith(item.href));

                          // If item has permission requirement, wrap with Can component
                          if (item.permission) {
                            return (
                              <Can key={item.href} I={item.permission}>
                                <li>
                                  <Link
                                    href={item.href}
                                    className={`flex items-center gap-3 rounded-lg px-3 py-1.5 ml-2 text-sm transition-colors ${
                                      isItemActive
                                        ? 'bg-sky-500/10 text-sky-400'
                                        : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                                    }`}
                                    onClick={() => setSidebarOpen(false)}
                                  >
                                    <item.icon className="h-4 w-4 flex-shrink-0" />
                                    <span>{item.name}</span>
                                    {item.badge && (
                                      <span className="ml-auto bg-sky-500/20 text-sky-400 text-xs px-2 py-0.5 rounded-full">
                                        {item.badge}
                                      </span>
                                    )}
                                  </Link>
                                </li>
                              </Can>
                            );
                          }

                          // No permission requirement, show by default
                          return (
                            <li key={item.href}>
                              <Link
                                href={item.href}
                                className={`flex items-center gap-3 rounded-lg px-3 py-1.5 ml-2 text-sm transition-colors ${
                                  isItemActive
                                    ? 'bg-sky-500/10 text-sky-400'
                                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                                }`}
                                onClick={() => setSidebarOpen(false)}
                              >
                                <item.icon className="h-4 w-4 flex-shrink-0" />
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
                    )}
                  </div>
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