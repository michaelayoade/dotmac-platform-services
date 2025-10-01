"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Home,
  Users,
  DollarSign,
  UserPlus,
  Settings,
  LogOut,
  Menu,
  X,
  Handshake,
  BarChart3,
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
}

const navigation: NavItem[] = [
  { name: "Dashboard", href: "/portal/dashboard", icon: Home },
  { name: "Referrals", href: "/portal/referrals", icon: UserPlus },
  { name: "Commissions", href: "/portal/commissions", icon: DollarSign },
  { name: "Customers", href: "/portal/customers", icon: Users },
  { name: "Performance", href: "/portal/performance", icon: BarChart3 },
  { name: "Settings", href: "/portal/settings", icon: Settings },
];

export default function PartnerPortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [partner, setPartner] = useState<{ company_name?: string; partner_number?: string } | null>(null);
  const pathname = usePathname();
  const router = useRouter();

  // Skip auth check for login page
  useEffect(() => {
    if (pathname !== "/portal/login" && pathname !== "/portal/register") {
      fetchPartnerProfile();
    }
  }, [pathname]);

  const fetchPartnerProfile = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/partners/portal/profile`, {
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        // Not authenticated, redirect to login
        router.push("/portal/login");
        return;
      }

      const data = await response.json();
      setPartner(data);
    } catch (error) {
      console.error("Failed to fetch partner profile:", error);
      router.push("/portal/login");
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE}/api/v1/partners/portal/logout`, {
        method: "POST",
        credentials: "include",
      });
      router.push("/portal/login");
    } catch (error) {
      console.error("Logout error:", error);
      router.push("/portal/login");
    }
  };

  // Don't show layout for login/register pages
  if (pathname === "/portal/login" || pathname === "/portal/register") {
    return <>{children}</>;
  }

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
            <div className="flex items-center ml-4 lg:ml-0 gap-3">
              <div className="flex items-center justify-center w-10 h-10 bg-blue-600 rounded-lg">
                <Handshake className="w-6 h-6 text-white" />
              </div>
              <div>
                <div className="text-lg font-semibold text-white">Partner Portal</div>
                <div className="text-xs text-slate-400">{partner?.company_name}</div>
              </div>
            </div>
          </div>

          {/* Right side - User menu */}
          <div className="flex items-center gap-4">
            <div className="hidden md:block text-sm text-slate-400">
              {partner?.partner_number && `#${partner.partner_number}`}
            </div>
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-300 hover:bg-slate-800 transition-colors"
              >
                <span>{partner?.company_name || "Partner"}</span>
              </button>

              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-56 rounded-md bg-slate-800 shadow-lg ring-1 ring-black ring-opacity-5">
                  <div className="py-1">
                    <div className="px-4 py-2 text-sm text-slate-400">
                      <div className="font-semibold text-slate-200">
                        {partner?.company_name}
                      </div>
                      <div className="text-xs">{partner?.partner_number}</div>
                    </div>
                    <hr className="my-1 border-slate-700" />
                    <Link
                      href="/portal/settings"
                      className="block px-4 py-2 text-sm text-slate-300 hover:bg-slate-700"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      Settings
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
      <div
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-slate-900 pt-16 transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
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
              const isActive = pathname === item.href;

              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-blue-600 text-white"
                        : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
                    }`}
                    onClick={() => setSidebarOpen(false)}
                  >
                    <item.icon className="h-5 w-5 flex-shrink-0" />
                    <span>{item.name}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>

        {/* Bottom section */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-800">
          <div className="text-xs text-slate-500">
            <div>Need help?</div>
            <a
              href="mailto:partners@dotmac.com"
              className="text-blue-400 hover:text-blue-300"
            >
              Contact Support
            </a>
          </div>
        </div>
      </div>

      {/* Main content area */}
      <div className="lg:pl-64 pt-16">
        <main className="min-h-screen">{children}</main>
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
