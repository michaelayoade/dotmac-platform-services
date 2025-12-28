"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Search,
  Bell,
  ChevronDown,
  LogOut,
  User,
  Settings,
  Shield,
  Menu,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useTenant, useFocusTrap } from "@/lib/hooks";
import { ThemeToggleSimple } from "@/components/shared/theme-toggle";
import { api } from "@/lib/api/client";
import type { PlatformUser } from "@/types/auth";

interface HeaderProps {
  user: PlatformUser;
  onCommandPaletteOpen: () => void;
  onMobileMenuOpen?: () => void;
}

export function Header({ user, onCommandPaletteOpen, onMobileMenuOpen }: HeaderProps) {
  const router = useRouter();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const { currentTenant, tenants, switchTenant } = useTenant();
  const userInitial = (
    user.fullName?.charAt(0) ||
    user.username?.charAt(0) ||
    user.email?.charAt(0) ||
    "U"
  ).toUpperCase();

  const userMenuRef = useRef<HTMLDivElement>(null);
  const notificationsRef = useRef<HTMLDivElement>(null);

  // Focus traps for dropdown menus
  const notificationDropdownRef = useFocusTrap<HTMLDivElement>({
    enabled: showNotifications,
    onEscape: () => setShowNotifications(false),
    restoreFocusOnClose: true,
  });

  const userMenuDropdownRef = useFocusTrap<HTMLDivElement>({
    enabled: showUserMenu,
    onEscape: () => setShowUserMenu(false),
    restoreFocusOnClose: true,
  });

  // Keyboard shortcut for command palette
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        onCommandPaletteOpen();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onCommandPaletteOpen]);

  // Close menus when clicking outside - single listener, ref-based check
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as Node;
      if (userMenuRef.current && !userMenuRef.current.contains(target)) {
        setShowUserMenu(false);
      }
      if (notificationsRef.current && !notificationsRef.current.contains(target)) {
        setShowNotifications(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = useCallback(async () => {
    try {
      await api.post("/api/v1/auth/logout");
    } catch (error) {
      console.error("Logout failed:", error);
    } finally {
      router.push("/login");
    }
  }, [router]);

  return (
    <header className="sticky top-0 z-30 h-16 bg-surface/80 backdrop-blur-lg border-b border-border">
      <div className="flex items-center justify-between h-full px-6">
        {/* Left section - Mobile menu + Search trigger */}
        <div className="flex items-center gap-4">
          {/* Mobile menu button */}
          {onMobileMenuOpen && (
            <button
              onClick={onMobileMenuOpen}
              className="lg:hidden p-2 rounded-md text-text-muted hover:text-text-secondary hover:bg-surface-overlay transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent"
              aria-label="Open navigation menu"
            >
              <Menu className="w-5 h-5" aria-hidden="true" />
            </button>
          )}

          {/* Command palette trigger */}
          <button
            onClick={onCommandPaletteOpen}
            className="command-trigger"
          >
            <Search className="w-4 h-4" />
            <span className="hidden sm:inline">Search...</span>
            <kbd className="hidden sm:inline-flex">⌘K</kbd>
          </button>
        </div>

        {/* Center - Tenant selector (if multi-tenant) */}
        {tenants && tenants.length > 1 && (
          <div className="hidden md:flex items-center">
            <label htmlFor="tenant-selector" className="sr-only">
              Select tenant
            </label>
            <select
              id="tenant-selector"
              value={currentTenant?.id}
              onChange={(e) => switchTenant(e.target.value)}
              className="bg-surface-overlay border border-border rounded-md px-3 py-1.5 text-sm text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-surface"
            >
              {tenants.map((tenant) => (
                <option key={tenant.id} value={tenant.id}>
                  {tenant.name}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Right section */}
        <div className="flex items-center gap-1 sm:gap-2">
          {/* Live indicator */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md bg-surface-overlay text-sm">
            <span className="live-indicator text-text-muted">Live</span>
          </div>

          {/* Notifications */}
          <div className="relative" ref={notificationsRef}>
            <button
              onClick={() => {
                setShowNotifications(!showNotifications);
                setShowUserMenu(false);
              }}
              className={cn(
                "relative p-2 rounded-md transition-colors",
                "text-text-muted hover:text-text-secondary hover:bg-surface-overlay",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                showNotifications && "bg-surface-overlay text-text-secondary"
              )}
              aria-label="Notifications"
              aria-expanded={showNotifications}
              aria-haspopup="menu"
              aria-controls="notifications-menu"
            >
              <Bell className="w-5 h-5" aria-hidden="true" />
              {/* Notification badge */}
              <span
                className="absolute top-1 right-1 w-2 h-2 bg-status-error rounded-full"
                role="status"
                aria-label="You have unread notifications"
              >
                <span className="sr-only">3 unread notifications</span>
              </span>
            </button>

            {/* Notifications dropdown */}
            {showNotifications && (
              <div
                id="notifications-menu"
                role="menu"
                aria-label="Notifications"
                ref={notificationDropdownRef}
                className="absolute right-0 mt-2 w-[calc(100vw-2rem)] sm:w-80 max-w-80 bg-surface-elevated border border-border rounded-lg shadow-lg overflow-hidden animate-fade-in"
              >
                <div className="px-4 py-3 border-b border-border">
                  <h3 className="text-sm font-semibold text-text-primary">
                    Notifications
                  </h3>
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {[1, 2, 3].map((i) => (
                    <button
                      key={i}
                      role="menuitem"
                      className="w-full px-4 py-3 hover:bg-surface-overlay cursor-pointer border-b border-border-subtle last:border-0 text-left focus:outline-none focus:bg-surface-overlay"
                    >
                      <p className="text-sm text-text-primary">
                        New deployment completed
                      </p>
                      <p className="text-xs text-text-muted mt-1">2 min ago</p>
                    </button>
                  ))}
                </div>
                <div className="px-4 py-2 border-t border-border">
                  <button
                    role="menuitem"
                    className="text-sm text-accent hover:text-accent-hover focus:outline-none focus:underline"
                  >
                    View all notifications
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Theme toggle */}
          <ThemeToggleSimple />

          {/* Divider */}
          <div className="w-px h-6 bg-border mx-1" />

          {/* User menu */}
          <div className="relative" ref={userMenuRef}>
            <button
              onClick={() => {
                setShowUserMenu(!showUserMenu);
                setShowNotifications(false);
              }}
              className={cn(
                "flex items-center gap-2 px-2 py-1.5 rounded-md transition-colors",
                "hover:bg-surface-overlay",
                "focus:outline-none focus-visible:ring-2 focus-visible:ring-accent",
                showUserMenu && "bg-surface-overlay"
              )}
              aria-label={`User menu for ${user.fullName || user.username || user.email || "user"}`}
              aria-expanded={showUserMenu}
              aria-haspopup="menu"
              aria-controls="user-menu"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent to-highlight flex items-center justify-center text-sm font-semibold text-text-inverse">
                {userInitial}
              </div>
              <ChevronDown
                className={cn(
                  "w-4 h-4 text-text-muted transition-transform",
                  showUserMenu && "rotate-180"
                )}
                aria-hidden="true"
              />
            </button>

            {/* User dropdown */}
            {showUserMenu && (
              <div
                id="user-menu"
                role="menu"
                aria-label="User menu"
                ref={userMenuDropdownRef}
                className="absolute right-0 mt-2 w-[calc(100vw-2rem)] sm:w-56 max-w-56 bg-surface-elevated border border-border rounded-lg shadow-lg overflow-hidden animate-fade-in"
              >
                {/* User info */}
                <div className="px-4 py-3 border-b border-border">
                  <p className="text-sm font-medium text-text-primary">
                    {user.fullName || user.username}
                  </p>
                  <p className="text-xs text-text-muted truncate">
                    {user.email}
                  </p>
                </div>

                {/* Menu items */}
                <div className="py-1">
                  <button
                    role="menuitem"
                    className="w-full flex items-center gap-3 px-4 py-2 text-sm text-text-secondary hover:bg-surface-overlay hover:text-text-primary focus:outline-none focus:bg-surface-overlay"
                  >
                    <User className="w-4 h-4" aria-hidden="true" />
                    Profile
                  </button>
                  <button
                    role="menuitem"
                    className="w-full flex items-center gap-3 px-4 py-2 text-sm text-text-secondary hover:bg-surface-overlay hover:text-text-primary focus:outline-none focus:bg-surface-overlay"
                  >
                    <Settings className="w-4 h-4" aria-hidden="true" />
                    Settings
                  </button>
                  <button
                    role="menuitem"
                    className="w-full flex items-center gap-3 px-4 py-2 text-sm text-text-secondary hover:bg-surface-overlay hover:text-text-primary focus:outline-none focus:bg-surface-overlay"
                  >
                    <Shield className="w-4 h-4" aria-hidden="true" />
                    Security
                  </button>
                </div>

                {/* Sign out */}
                <div className="border-t border-border py-1">
                  <button
                    onClick={handleLogout}
                    role="menuitem"
                    className="w-full flex items-center gap-3 px-4 py-2 text-sm text-status-error hover:bg-status-error/15 focus:outline-none focus:bg-status-error/15"
                  >
                    <LogOut className="w-4 h-4" aria-hidden="true" />
                    Sign out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
