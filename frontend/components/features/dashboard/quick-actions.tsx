"use client";

import { useState, type ElementType } from "react";
import { useRouter } from "next/navigation";
import { Plus, UserPlus, Building2, FileText, Server, ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";

interface QuickAction {
  label: string;
  icon: ElementType;
  href: string;
  description: string;
}

const actions: QuickAction[] = [
  {
    label: "New User",
    icon: UserPlus,
    href: "/users/new",
    description: "Invite a new user",
  },
  {
    label: "New Tenant",
    icon: Building2,
    href: "/tenants/new",
    description: "Create an organization",
  },
  {
    label: "New Invoice",
    icon: FileText,
    href: "/billing/invoices/new",
    description: "Generate an invoice",
  },
  {
    label: "New Deployment",
    icon: Server,
    href: "/deployments/new",
    description: "Deploy an instance",
  },
];

export function QuickActions() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "inline-flex items-center gap-2 px-4 py-2.5 rounded-lg",
          "bg-accent text-text-inverse font-medium text-sm",
          "hover:bg-accent-hover",
          "shadow-glow-sm hover:shadow-glow",
          "transition-all duration-200"
        )}
      >
        <Plus className="w-4 h-4" />
        Quick Action
        <ChevronDown
          className={cn(
            "w-4 h-4 transition-transform",
            isOpen && "rotate-180"
          )}
        />
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 mt-2 w-64 bg-surface-elevated border border-border rounded-lg shadow-lg overflow-hidden z-20 animate-fade-in">
            <div className="py-1">
              {actions.map((action) => {
                const Icon = action.icon;
                return (
                  <button
                    key={action.href}
                    onClick={() => {
                      router.push(action.href);
                      setIsOpen(false);
                    }}
                    className="w-full flex items-start gap-3 px-4 py-3 hover:bg-surface-overlay transition-colors"
                  >
                    <div className="p-2 rounded-md bg-accent-subtle">
                      <Icon className="w-4 h-4 text-accent" />
                    </div>
                    <div className="text-left">
                      <p className="text-sm font-medium text-text-primary">
                        {action.label}
                      </p>
                      <p className="text-xs text-text-muted">
                        {action.description}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
