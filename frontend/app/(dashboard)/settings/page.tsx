import Link from "next/link";
import type { ElementType } from "react";
import {
  User,
  Shield,
  Bell,
  CreditCard,
  Key,
  Palette,
  Globe,
  Building2,
  ChevronRight,
} from "lucide-react";

import { cn } from "@/lib/utils";

export const metadata = {
  title: "Settings",
  description: "Manage your account and platform settings",
};

interface SettingsSection {
  title: string;
  description: string;
  icon: ElementType;
  href: string;
  items?: string[];
}

const settingsSections: SettingsSection[] = [
  {
    title: "Profile",
    description: "Manage your personal information and preferences",
    icon: User,
    href: "/settings/profile",
    items: ["Name & avatar", "Email address", "Language", "Timezone"],
  },
  {
    title: "Security",
    description: "Protect your account with advanced security features",
    icon: Shield,
    href: "/settings/security",
    items: ["Password", "Two-factor authentication", "Active sessions", "Login history"],
  },
  {
    title: "Notifications",
    description: "Configure how and when you receive notifications",
    icon: Bell,
    href: "/settings/notifications",
    items: ["Email notifications", "Push notifications", "Slack integration", "Webhook alerts"],
  },
  {
    title: "API Keys",
    description: "Manage API keys for programmatic access",
    icon: Key,
    href: "/settings/api-keys",
    items: ["Create API key", "Rotate keys", "Key permissions", "Usage limits"],
  },
  {
    title: "Billing",
    description: "Manage payment methods and view billing history",
    icon: CreditCard,
    href: "/settings/billing",
    items: ["Payment methods", "Billing history", "Invoices", "Tax information"],
  },
  {
    title: "Appearance",
    description: "Customize the look and feel of your dashboard",
    icon: Palette,
    href: "/settings/appearance",
    items: ["Theme", "Color scheme", "Density", "Sidebar layout"],
  },
  {
    title: "Organization",
    description: "Manage organization settings and team members",
    icon: Building2,
    href: "/settings/organization",
    items: ["Team members", "Roles & permissions", "SSO configuration", "Domain verification"],
  },
  {
    title: "Integrations",
    description: "Connect with external services and tools",
    icon: Globe,
    href: "/settings/integrations",
    items: ["Slack", "GitHub", "Jira", "Custom webhooks"],
  },
];

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header border-0 pb-0 mb-0">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-description">
            Manage your account, security, and platform preferences
          </p>
        </div>
      </div>

      {/* Settings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {settingsSections.map((section, index) => (
          <SettingsCard key={section.href} section={section} index={index} />
        ))}
      </div>
    </div>
  );
}

function SettingsCard({ section, index }: { section: SettingsSection; index: number }) {
  const Icon = section.icon;

  return (
    <Link
      href={section.href}
      className={cn(
        "card card--interactive p-6 group animate-fade-up",
      )}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex items-start gap-4">
        {/* Icon */}
        <div className="p-3 rounded-lg bg-accent-subtle group-hover:bg-accent/20 transition-colors">
          <Icon className="w-5 h-5 text-accent" />
        </div>

        {/* Content */}
        <div className="flex-1">
          <div className="flex items-center justify-between mb-1">
            <h3 className="font-semibold text-text-primary group-hover:text-accent transition-colors">
              {section.title}
            </h3>
            <ChevronRight className="w-4 h-4 text-text-muted group-hover:text-accent group-hover:translate-x-0.5 transition-all" />
          </div>
          <p className="text-sm text-text-muted mb-3">{section.description}</p>

          {/* Items preview */}
          {section.items && (
            <div className="flex flex-wrap gap-1.5">
              {section.items.slice(0, 3).map((item) => (
                <span
                  key={item}
                  className="text-2xs px-2 py-0.5 rounded-full bg-surface-overlay text-text-muted"
                >
                  {item}
                </span>
              ))}
              {section.items.length > 3 && (
                <span className="text-2xs px-2 py-0.5 rounded-full bg-surface-overlay text-text-muted">
                  +{section.items.length - 3} more
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}
