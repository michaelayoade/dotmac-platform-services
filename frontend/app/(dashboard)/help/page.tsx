"use client";

import {
  Book,
  MessageCircle,
  FileText,
  ExternalLink,
  Search,
  ChevronRight,
  Mail,
  Phone,
  HelpCircle,
  Zap,
  Users,
  Server,
  CreditCard,
  Shield,
} from "lucide-react";

import { PageHeader } from "@/components/shared/page-header";
import { Card, Button, Input } from "@dotmac/core";
import { cn } from "@/lib/utils";
import { useState } from "react";

interface HelpCategory {
  id: string;
  title: string;
  description: string;
  icon: typeof Book;
  articles: HelpArticle[];
}

interface HelpArticle {
  id: string;
  title: string;
  description: string;
  href: string;
}

const helpCategories: HelpCategory[] = [
  {
    id: "getting-started",
    title: "Getting Started",
    description: "Learn the basics of using the platform",
    icon: Zap,
    articles: [
      {
        id: "gs-1",
        title: "Platform Overview",
        description: "Introduction to key concepts and navigation",
        href: "/docs/overview",
      },
      {
        id: "gs-2",
        title: "Quick Start Guide",
        description: "Get up and running in 5 minutes",
        href: "/docs/quickstart",
      },
      {
        id: "gs-3",
        title: "Dashboard Walkthrough",
        description: "Understanding your dashboard metrics",
        href: "/docs/dashboard",
      },
    ],
  },
  {
    id: "user-management",
    title: "User Management",
    description: "Managing users, roles, and permissions",
    icon: Users,
    articles: [
      {
        id: "um-1",
        title: "Inviting Team Members",
        description: "How to add new users to your organization",
        href: "/docs/users/invite",
      },
      {
        id: "um-2",
        title: "Role-Based Access Control",
        description: "Configure permissions and access levels",
        href: "/docs/users/rbac",
      },
      {
        id: "um-3",
        title: "Managing User Sessions",
        description: "Session management and security",
        href: "/docs/users/sessions",
      },
    ],
  },
  {
    id: "tenants",
    title: "Tenant Management",
    description: "Multi-tenant configuration and setup",
    icon: Server,
    articles: [
      {
        id: "tm-1",
        title: "Creating Tenants",
        description: "Set up new tenant organizations",
        href: "/docs/tenants/create",
      },
      {
        id: "tm-2",
        title: "Tenant Settings",
        description: "Configure tenant-specific options",
        href: "/docs/tenants/settings",
      },
      {
        id: "tm-3",
        title: "Tenant Isolation",
        description: "Understanding data isolation",
        href: "/docs/tenants/isolation",
      },
    ],
  },
  {
    id: "billing",
    title: "Billing & Subscriptions",
    description: "Payment methods, invoices, and plans",
    icon: CreditCard,
    articles: [
      {
        id: "b-1",
        title: "Managing Subscriptions",
        description: "Upgrade, downgrade, or cancel plans",
        href: "/docs/billing/subscriptions",
      },
      {
        id: "b-2",
        title: "Invoice History",
        description: "View and download past invoices",
        href: "/docs/billing/invoices",
      },
      {
        id: "b-3",
        title: "Payment Methods",
        description: "Add or update payment information",
        href: "/docs/billing/payment-methods",
      },
    ],
  },
  {
    id: "security",
    title: "Security & Compliance",
    description: "Security features and best practices",
    icon: Shield,
    articles: [
      {
        id: "s-1",
        title: "Two-Factor Authentication",
        description: "Enable 2FA for your account",
        href: "/docs/security/2fa",
      },
      {
        id: "s-2",
        title: "API Key Management",
        description: "Create and manage API keys",
        href: "/docs/security/api-keys",
      },
      {
        id: "s-3",
        title: "Audit Logs",
        description: "Track activity and changes",
        href: "/docs/security/audit",
      },
    ],
  },
];

const quickLinks = [
  {
    title: "Documentation",
    description: "Browse the full documentation",
    icon: Book,
    href: "/docs",
    external: false,
  },
  {
    title: "API Reference",
    description: "Explore the API documentation",
    icon: FileText,
    href: "/api-docs",
    external: false,
  },
  {
    title: "Status Page",
    description: "Check system status",
    icon: Server,
    href: "/status",
    external: false,
  },
  {
    title: "Community Forum",
    description: "Get help from the community",
    icon: MessageCircle,
    href: "https://community.example.com",
    external: true,
  },
];

export default function HelpPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedCategory, setExpandedCategory] = useState<string | null>("getting-started");

  const filteredCategories = searchQuery
    ? helpCategories
        .map((category) => ({
          ...category,
          articles: category.articles.filter(
            (article) =>
              article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
              article.description.toLowerCase().includes(searchQuery.toLowerCase())
          ),
        }))
        .filter((category) => category.articles.length > 0)
    : helpCategories;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Help & Support"
        description="Find answers, browse documentation, and get support"
      />

      {/* Search */}
      <Card className="p-6">
        <div className="max-w-2xl mx-auto text-center">
          <HelpCircle className="w-12 h-12 text-accent mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-text-primary mb-2">How can we help you?</h2>
          <p className="text-text-muted mb-4">
            Search our knowledge base or browse categories below
          </p>
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
            <Input
              placeholder="Search for help articles..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-12 h-12 text-base"
            />
          </div>
        </div>
      </Card>

      {/* Quick Links */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {quickLinks.map((link) => {
          const Icon = link.icon;
          return (
            <Card
              key={link.title}
              className="p-4 hover:border-accent/50 transition-colors cursor-pointer group"
              onClick={() => {
                if (link.external) {
                  window.open(link.href, "_blank");
                } else {
                  window.location.href = link.href;
                }
              }}
            >
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-accent/15 group-hover:bg-accent/20 transition-colors">
                  <Icon className="w-5 h-5 text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1">
                    <p className="text-sm font-medium text-text-primary">{link.title}</p>
                    {link.external && (
                      <ExternalLink className="w-3 h-3 text-text-muted" />
                    )}
                  </div>
                  <p className="text-xs text-text-muted">{link.description}</p>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* Help Categories */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <h3 className="text-lg font-semibold text-text-primary">Browse by Topic</h3>
          {filteredCategories.length === 0 ? (
            <Card className="p-8 text-center">
              <HelpCircle className="w-12 h-12 text-text-muted mx-auto mb-4 opacity-50" />
              <p className="text-text-muted">No articles found for &quot;{searchQuery}&quot;</p>
            </Card>
          ) : (
            filteredCategories.map((category) => {
              const Icon = category.icon;
              const isExpanded = expandedCategory === category.id;

              return (
                <Card key={category.id} className="overflow-hidden">
                  <button
                    className="w-full p-4 flex items-center gap-4 hover:bg-surface-overlay/50 transition-colors text-left"
                    onClick={() =>
                      setExpandedCategory(isExpanded ? null : category.id)
                    }
                  >
                    <div className="p-2 rounded-lg bg-surface-overlay">
                      <Icon className="w-5 h-5 text-accent" />
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-text-primary">{category.title}</p>
                      <p className="text-sm text-text-muted">{category.description}</p>
                    </div>
                    <ChevronRight
                      className={cn(
                        "w-5 h-5 text-text-muted transition-transform",
                        isExpanded && "rotate-90"
                      )}
                    />
                  </button>
                  {isExpanded && (
                    <div className="border-t border-border">
                      {category.articles.map((article) => (
                        <a
                          key={article.id}
                          href={article.href}
                          className="block p-4 pl-16 hover:bg-surface-overlay/50 transition-colors border-t border-border first:border-t-0"
                        >
                          <p className="text-sm font-medium text-text-primary">
                            {article.title}
                          </p>
                          <p className="text-xs text-text-muted">{article.description}</p>
                        </a>
                      ))}
                    </div>
                  )}
                </Card>
              );
            })
          )}
        </div>

        {/* Contact Support */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-text-primary">Contact Support</h3>
          <Card className="p-6 space-y-6">
            <div>
              <h4 className="font-medium text-text-primary mb-2">Need more help?</h4>
              <p className="text-sm text-text-muted">
                Our support team is available to assist you with any questions or issues.
              </p>
            </div>

            <div className="space-y-3">
              <a
                href="mailto:support@example.com"
                className="flex items-center gap-3 p-3 rounded-lg bg-surface-overlay hover:bg-surface-overlay/80 transition-colors"
              >
                <Mail className="w-5 h-5 text-accent" />
                <div>
                  <p className="text-sm font-medium text-text-primary">Email Support</p>
                  <p className="text-xs text-text-muted">support@example.com</p>
                </div>
              </a>

              <a
                href="tel:+1-800-SUPPORT"
                className="flex items-center gap-3 p-3 rounded-lg bg-surface-overlay hover:bg-surface-overlay/80 transition-colors"
              >
                <Phone className="w-5 h-5 text-accent" />
                <div>
                  <p className="text-sm font-medium text-text-primary">Phone Support</p>
                  <p className="text-xs text-text-muted">Mon-Fri, 9am-5pm EST</p>
                </div>
              </a>

              <a
                href="/tickets/new"
                className="flex items-center gap-3 p-3 rounded-lg bg-surface-overlay hover:bg-surface-overlay/80 transition-colors"
              >
                <MessageCircle className="w-5 h-5 text-accent" />
                <div>
                  <p className="text-sm font-medium text-text-primary">Submit a Ticket</p>
                  <p className="text-xs text-text-muted">Get a response within 24h</p>
                </div>
              </a>
            </div>

            <div className="pt-4 border-t border-border">
              <p className="text-xs text-text-muted">
                For urgent issues, please call our support line or mark your ticket as high priority.
              </p>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-2 rounded-lg bg-status-success/15">
                <Server className="w-5 h-5 text-status-success" />
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary">System Status</p>
                <p className="text-xs text-status-success">All systems operational</p>
              </div>
            </div>
            <Button variant="outline" size="sm" className="w-full" onClick={() => window.location.href = "/status"}>
              View Status Page
            </Button>
          </Card>
        </div>
      </div>
    </div>
  );
}
