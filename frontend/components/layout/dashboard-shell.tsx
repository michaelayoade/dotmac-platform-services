"use client";

import { useState, useCallback, type ReactNode } from "react";

import { cn } from "@/lib/utils";
import { Sidebar, useSidebarState } from "./sidebar";
import { Header } from "./header";
import { CommandPalette } from "./command-palette";
import { SkipToContent } from "./skip-to-content";
import { MobileDrawer } from "./mobile-drawer";
import type { PlatformUser } from "@/types/auth";

interface DashboardShellProps {
  children: ReactNode;
  user: PlatformUser;
}

export function DashboardShell({ children, user }: DashboardShellProps) {
  // Use persisted sidebar state
  const {
    collapsed: sidebarCollapsed,
    toggleCollapsed: toggleSidebar,
    isHydrated,
  } = useSidebarState();

  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleMobileMenuOpen = useCallback(() => setMobileMenuOpen(true), []);
  const handleMobileMenuClose = useCallback(() => setMobileMenuOpen(false), []);
  const handleCommandPaletteOpen = useCallback(
    () => setCommandPaletteOpen(true),
    []
  );
  const handleCommandPaletteClose = useCallback(
    () => setCommandPaletteOpen(false),
    []
  );

  return (
    <div className="relative flex min-h-screen">
      {/* Skip to content link for keyboard users */}
      <SkipToContent targetId="main-content" />

      {/* Desktop Sidebar - hidden on mobile */}
      <div className="hidden lg:block">
        <Sidebar
          collapsed={sidebarCollapsed}
          onToggle={toggleSidebar}
          user={user}
          isHydrated={isHydrated}
        />
      </div>

      {/* Mobile Drawer */}
      <MobileDrawer
        open={mobileMenuOpen}
        onClose={handleMobileMenuClose}
        user={user}
      />

      {/* Main content area */}
      <div
        className={cn(
          "flex-1 flex flex-col",
          isHydrated ? "transition-all duration-300" : "transition-none",
          "ml-0",
          sidebarCollapsed ? "lg:ml-16" : "lg:ml-64"
        )}
      >
        {/* Header */}
        <Header
          user={user}
          onCommandPaletteOpen={handleCommandPaletteOpen}
          onMobileMenuOpen={handleMobileMenuOpen}
        />

        {/* Page content */}
        <main
          id="main-content"
          className="flex-1 p-4 sm:p-6 lg:p-8 overflow-auto"
          tabIndex={-1}
        >
          <div className="mx-auto max-w-7xl animate-fade-up">{children}</div>
        </main>
      </div>

      {/* Command Palette */}
      <CommandPalette
        open={commandPaletteOpen}
        onClose={handleCommandPaletteClose}
      />

      {/* Background decorative elements */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        {/* Subtle grid pattern */}
        <div className="absolute inset-0 bg-grid opacity-[0.02]" />

        {/* Accent glow in corner */}
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-accent/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-highlight/5 rounded-full blur-3xl" />
      </div>
    </div>
  );
}
