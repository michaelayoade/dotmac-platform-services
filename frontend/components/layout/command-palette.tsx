"use client";

import { useCallback, useEffect, useState, type ElementType, type KeyboardEvent } from "react";
import { useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  Building2,
  CreditCard,
  BarChart3,
  UserCircle,
  Server,
  Settings,
  Search,
  Plus,
  FileText,
  Clock,
} from "lucide-react";
import { Dialog, DialogContent, DialogOverlay } from "@dotmac/core";

import { cn } from "@/lib/utils";

interface CommandPaletteProps {
  open: boolean;
  onClose: () => void;
}

interface CommandItem {
  id: string;
  label: string;
  description?: string;
  icon: ElementType;
  action: () => void;
  keywords?: string[];
  section: "navigation" | "actions" | "recent";
}

export function CommandPalette({ open, onClose }: CommandPaletteProps) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);

  const commands: CommandItem[] = [
    // Recent
    {
      id: "recent-1",
      label: "Invoice #INV-2024-001",
      description: "Viewed 2 hours ago",
      icon: Clock,
      action: () => router.push("/billing/invoices/INV-2024-001"),
      section: "recent",
    },
    {
      id: "recent-2",
      label: "User: john.doe@example.com",
      description: "Viewed yesterday",
      icon: Clock,
      action: () => router.push("/users/abc123"),
      section: "recent",
    },
    // Navigation
    {
      id: "nav-dashboard",
      label: "Go to Dashboard",
      icon: LayoutDashboard,
      action: () => router.push("/"),
      keywords: ["home", "overview"],
      section: "navigation",
    },
    {
      id: "nav-users",
      label: "Go to Users",
      icon: Users,
      action: () => router.push("/users"),
      keywords: ["members", "team"],
      section: "navigation",
    },
    {
      id: "nav-tenants",
      label: "Go to Tenants",
      icon: Building2,
      action: () => router.push("/tenants"),
      keywords: ["organizations", "orgs"],
      section: "navigation",
    },
    {
      id: "nav-billing",
      label: "Go to Billing",
      icon: CreditCard,
      action: () => router.push("/billing"),
      keywords: ["invoices", "payments", "subscriptions"],
      section: "navigation",
    },
    {
      id: "nav-analytics",
      label: "Go to Analytics",
      icon: BarChart3,
      action: () => router.push("/analytics"),
      keywords: ["reports", "metrics", "stats"],
      section: "navigation",
    },
    {
      id: "nav-customers",
      label: "Go to Customers",
      icon: UserCircle,
      action: () => router.push("/customers"),
      keywords: ["crm", "contacts"],
      section: "navigation",
    },
    {
      id: "nav-deployments",
      label: "Go to Deployments",
      icon: Server,
      action: () => router.push("/deployments"),
      keywords: ["infrastructure", "instances"],
      section: "navigation",
    },
    {
      id: "nav-settings",
      label: "Go to Settings",
      icon: Settings,
      action: () => router.push("/settings"),
      keywords: ["config", "preferences"],
      section: "navigation",
    },
    // Actions
    {
      id: "action-new-user",
      label: "Create New User",
      icon: Plus,
      action: () => router.push("/users/new"),
      keywords: ["add user", "invite"],
      section: "actions",
    },
    {
      id: "action-new-tenant",
      label: "Create New Tenant",
      icon: Plus,
      action: () => router.push("/tenants/new"),
      keywords: ["add org", "organization"],
      section: "actions",
    },
    {
      id: "action-new-invoice",
      label: "Create New Invoice",
      icon: FileText,
      action: () => router.push("/billing/invoices/new"),
      keywords: ["bill", "charge"],
      section: "actions",
    },
  ];

  // Filter commands based on query
  const filteredCommands = query
    ? commands.filter((cmd) => {
        const searchStr = [cmd.label, cmd.description, ...(cmd.keywords || [])].join(" ").toLowerCase();
        return searchStr.includes(query.toLowerCase());
      })
    : commands;

  // Group by section
  const groupedCommands = {
    recent: filteredCommands.filter((c) => c.section === "recent"),
    actions: filteredCommands.filter((c) => c.section === "actions"),
    navigation: filteredCommands.filter((c) => c.section === "navigation"),
  };

  const flatCommands = [
    ...groupedCommands.recent,
    ...groupedCommands.actions,
    ...groupedCommands.navigation,
  ];

  // Reset selection when query changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Keyboard navigation
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (flatCommands.length === 0) {
        if (e.key === "Escape") {
          e.preventDefault();
          onClose();
        }
        return;
      }

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex((i) => (i + 1) % flatCommands.length);
          break;
        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex((i) => (i - 1 + flatCommands.length) % flatCommands.length);
          break;
        case "Enter":
          e.preventDefault();
          if (flatCommands[selectedIndex]) {
            flatCommands[selectedIndex].action();
            onClose();
          }
          break;
        case "Escape":
          e.preventDefault();
          onClose();
          break;
      }
    },
    [flatCommands, selectedIndex, onClose]
  );

  // Reset state when closing
  useEffect(() => {
    if (!open) {
      setQuery("");
      setSelectedIndex(0);
    }
  }, [open]);

  if (!open) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogOverlay className="bg-surface/80 backdrop-blur-sm" />
      <DialogContent
        className="fixed top-[20%] left-1/2 -translate-x-1/2 w-full max-w-xl bg-surface-elevated border border-border rounded-xl shadow-2xl overflow-hidden animate-scale-in"
        onKeyDown={handleKeyDown}
      >
        {/* Search input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-border">
          <Search className="w-5 h-5 text-text-muted flex-shrink-0" />
          <input
            type="text"
            placeholder="Search commands, pages, or actions..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-text-primary placeholder:text-text-muted focus:outline-none text-base"
            autoFocus
          />
          <kbd className="px-2 py-1 text-xs font-mono text-text-muted bg-surface rounded border border-border">
            ESC
          </kbd>
        </div>

        {/* Results */}
        <div className="max-h-80 overflow-y-auto py-2">
          {flatCommands.length === 0 ? (
            <div className="px-4 py-8 text-center text-text-muted">
              <p>No results found for "{query}"</p>
            </div>
          ) : (
            <>
              {/* Recent */}
              {groupedCommands.recent.length > 0 && (
                <div className="mb-2">
                  <div className="px-4 py-1">
                    <span className="text-2xs font-semibold uppercase tracking-wider text-text-muted">
                      Recent
                    </span>
                  </div>
                  {groupedCommands.recent.map((cmd, idx) => (
                    <CommandRow
                      key={cmd.id}
                      command={cmd}
                      selected={flatCommands.indexOf(cmd) === selectedIndex}
                      onClick={() => {
                        cmd.action();
                        onClose();
                      }}
                    />
                  ))}
                </div>
              )}

              {/* Actions */}
              {groupedCommands.actions.length > 0 && (
                <div className="mb-2">
                  <div className="px-4 py-1">
                    <span className="text-2xs font-semibold uppercase tracking-wider text-text-muted">
                      Actions
                    </span>
                  </div>
                  {groupedCommands.actions.map((cmd) => (
                    <CommandRow
                      key={cmd.id}
                      command={cmd}
                      selected={flatCommands.indexOf(cmd) === selectedIndex}
                      onClick={() => {
                        cmd.action();
                        onClose();
                      }}
                    />
                  ))}
                </div>
              )}

              {/* Navigation */}
              {groupedCommands.navigation.length > 0 && (
                <div>
                  <div className="px-4 py-1">
                    <span className="text-2xs font-semibold uppercase tracking-wider text-text-muted">
                      Navigation
                    </span>
                  </div>
                  {groupedCommands.navigation.map((cmd) => (
                    <CommandRow
                      key={cmd.id}
                      command={cmd}
                      selected={flatCommands.indexOf(cmd) === selectedIndex}
                      onClick={() => {
                        cmd.action();
                        onClose();
                      }}
                    />
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-2 border-t border-border text-2xs text-text-muted">
          <div className="flex items-center gap-4">
            <span>
              <kbd className="px-1.5 py-0.5 rounded bg-surface border border-border mr-1">↑↓</kbd>
              Navigate
            </span>
            <span>
              <kbd className="px-1.5 py-0.5 rounded bg-surface border border-border mr-1">↵</kbd>
              Select
            </span>
          </div>
          <span>
            <kbd className="px-1.5 py-0.5 rounded bg-surface border border-border mr-1">ESC</kbd>
            Close
          </span>
        </div>
      </DialogContent>
    </Dialog>
  );
}

function CommandRow({
  command,
  selected,
  onClick,
}: {
  command: CommandItem;
  selected: boolean;
  onClick: () => void;
}) {
  const Icon = command.icon;

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors",
        selected ? "bg-accent-subtle text-accent" : "text-text-secondary hover:bg-surface-overlay"
      )}
    >
      <Icon className={cn("w-4 h-4 flex-shrink-0", selected ? "text-accent" : "text-text-muted")} />
      <div className="flex-1 min-w-0">
        <p className={cn("text-sm font-medium", selected && "text-accent")}>{command.label}</p>
        {command.description && (
          <p className="text-xs text-text-muted truncate">{command.description}</p>
        )}
      </div>
    </button>
  );
}
