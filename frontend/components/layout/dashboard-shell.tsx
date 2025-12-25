"use client";

import { useState, type ReactNode } from "react";

import { Sidebar } from "./sidebar";
import { Header } from "./header";
import { CommandPalette } from "./command-palette";
import type { PlatformUser } from "@/types/auth";

interface DashboardShellProps {
  children: ReactNode;
  user: PlatformUser;
}

export function DashboardShell({ children, user }: DashboardShellProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  return (
    <div className="relative flex min-h-screen">
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        user={user}
      />

      {/* Main content area */}
      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${
          sidebarCollapsed ? "ml-16" : "ml-64"
        }`}
      >
        {/* Header */}
        <Header
          user={user}
          onCommandPaletteOpen={() => setCommandPaletteOpen(true)}
        />

        {/* Page content */}
        <main className="flex-1 p-6 overflow-auto">
          <div className="mx-auto max-w-7xl animate-fade-up">{children}</div>
        </main>
      </div>

      {/* Command Palette */}
      <CommandPalette
        open={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
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
