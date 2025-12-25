"use client";

import { useState, type ReactNode } from "react";

import { PortalSidebar, type PortalConfig } from "./portal-sidebar";
import { cn } from "@/lib/utils";
import type { PlatformUser } from "@/types/auth";

interface PortalShellProps {
  children: ReactNode;
  user: PlatformUser;
  config: PortalConfig;
}

export function PortalShell({ children, user, config }: PortalShellProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div className="relative flex min-h-screen bg-surface">
      {/* Portal Sidebar */}
      <PortalSidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        user={user}
        config={config}
      />

      {/* Main content area */}
      <div
        className={cn(
          "flex-1 flex flex-col transition-all duration-300",
          sidebarCollapsed ? "ml-16" : "ml-64"
        )}
      >
        {/* Page content */}
        <main className="flex-1 p-6 overflow-auto">
          <div className="mx-auto max-w-7xl animate-fade-up">{children}</div>
        </main>
      </div>

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
