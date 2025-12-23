"use client";

import { useEffect, useState } from "react";
import type { Session } from "next-auth";
import { signOut } from "next-auth/react";
import {
  Search,
  Bell,
  ChevronDown,
  LogOut,
  User,
  Settings,
  Shield,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { useTenant } from "@/lib/hooks/use-tenant";
import { ThemeToggle } from "@/components/shared/theme-toggle";

interface HeaderProps {
  session: Session;
  onCommandPaletteOpen: () => void;
}

export function Header({ session, onCommandPaletteOpen }: HeaderProps) {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const { currentTenant, tenants, switchTenant } = useTenant();

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

  // Close menus when clicking outside
  useEffect(() => {
    const handleClick = () => {
      setShowUserMenu(false);
      setShowNotifications(false);
    };

    if (showUserMenu || showNotifications) {
      document.addEventListener("click", handleClick);
      return () => document.removeEventListener("click", handleClick);
    }
  }, [showUserMenu, showNotifications]);

  return (
    <header className="sticky top-0 z-30 h-16 bg-surface/80 backdrop-blur-lg border-b border-border">
      <div className="flex items-center justify-between h-full px-6">
        {/* Left section - Breadcrumb / Search trigger */}
        <div className="flex items-center gap-4">
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
            <select
              value={currentTenant?.id}
              onChange={(e) => switchTenant(e.target.value)}
              className="bg-surface-overlay border border-border rounded-md px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent"
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
        <div className="flex items-center gap-2">
          {/* Live indicator */}
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md bg-surface-overlay text-sm">
            <span className="live-indicator text-text-muted">Live</span>
          </div>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowNotifications(!showNotifications);
                setShowUserMenu(false);
              }}
              className={cn(
                "relative p-2 rounded-md transition-colors",
                "text-text-muted hover:text-text-secondary hover:bg-surface-overlay",
                showNotifications && "bg-surface-overlay text-text-secondary"
              )}
            >
              <Bell className="w-5 h-5" />
              {/* Notification badge */}
              <span className="absolute top-1 right-1 w-2 h-2 bg-status-error rounded-full" />
            </button>

            {/* Notifications dropdown */}
            {showNotifications && (
              <div
                className="absolute right-0 mt-2 w-80 bg-surface-elevated border border-border rounded-lg shadow-lg overflow-hidden animate-fade-in"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="px-4 py-3 border-b border-border">
                  <h3 className="text-sm font-semibold text-text-primary">
                    Notifications
                  </h3>
                </div>
                <div className="max-h-80 overflow-y-auto">
                  {[1, 2, 3].map((i) => (
                    <div
                      key={i}
                      className="px-4 py-3 hover:bg-surface-overlay cursor-pointer border-b border-border-subtle last:border-0"
                    >
                      <p className="text-sm text-text-primary">
                        New deployment completed
                      </p>
                      <p className="text-xs text-text-muted mt-1">2 min ago</p>
                    </div>
                  ))}
                </div>
                <div className="px-4 py-2 border-t border-border">
                  <button className="text-sm text-accent hover:text-accent-hover">
                    View all notifications
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Theme toggle */}
          <ThemeToggle />

          {/* Divider */}
          <div className="w-px h-6 bg-border mx-1" />

          {/* User menu */}
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setShowUserMenu(!showUserMenu);
                setShowNotifications(false);
              }}
              className={cn(
                "flex items-center gap-2 px-2 py-1.5 rounded-md transition-colors",
                "hover:bg-surface-overlay",
                showUserMenu && "bg-surface-overlay"
              )}
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent to-highlight flex items-center justify-center text-sm font-semibold text-text-inverse">
                {session.user?.name?.charAt(0).toUpperCase() || "U"}
              </div>
              <ChevronDown
                className={cn(
                  "w-4 h-4 text-text-muted transition-transform",
                  showUserMenu && "rotate-180"
                )}
              />
            </button>

            {/* User dropdown */}
            {showUserMenu && (
              <div
                className="absolute right-0 mt-2 w-56 bg-surface-elevated border border-border rounded-lg shadow-lg overflow-hidden animate-fade-in"
                onClick={(e) => e.stopPropagation()}
              >
                {/* User info */}
                <div className="px-4 py-3 border-b border-border">
                  <p className="text-sm font-medium text-text-primary">
                    {session.user?.name}
                  </p>
                  <p className="text-xs text-text-muted truncate">
                    {session.user?.email}
                  </p>
                </div>

                {/* Menu items */}
                <div className="py-1">
                  <button className="w-full flex items-center gap-3 px-4 py-2 text-sm text-text-secondary hover:bg-surface-overlay hover:text-text-primary">
                    <User className="w-4 h-4" />
                    Profile
                  </button>
                  <button className="w-full flex items-center gap-3 px-4 py-2 text-sm text-text-secondary hover:bg-surface-overlay hover:text-text-primary">
                    <Settings className="w-4 h-4" />
                    Settings
                  </button>
                  <button className="w-full flex items-center gap-3 px-4 py-2 text-sm text-text-secondary hover:bg-surface-overlay hover:text-text-primary">
                    <Shield className="w-4 h-4" />
                    Security
                  </button>
                </div>

                {/* Sign out */}
                <div className="border-t border-border py-1">
                  <button
                    onClick={() => signOut()}
                    className="w-full flex items-center gap-3 px-4 py-2 text-sm text-status-error hover:bg-status-error/10"
                  >
                    <LogOut className="w-4 h-4" />
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
