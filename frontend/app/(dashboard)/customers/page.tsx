import { Suspense } from "react";
import Link from "next/link";
import {
  Plus,
  Download,
  Search,
  Filter,
  MoreHorizontal,
  Mail,
  Phone,
  Building2,
  MapPin,
  DollarSign,
  Calendar,
  ExternalLink,
  Star,
  TrendingUp,
} from "lucide-react";
import { DataTable, type ColumnDef } from "@dotmac/data-table";
import { Button } from "@dotmac/core";

import { cn } from "@/lib/utils";

export const metadata = {
  title: "Customers",
  description: "Customer relationship management",
};

interface Customer {
  id: string;
  name: string;
  email: string;
  company: string;
  phone?: string;
  location?: string;
  status: "active" | "churned" | "prospect" | "lead";
  tier: "enterprise" | "professional" | "starter";
  totalRevenue: number;
  lastContact: string;
  createdAt: string;
  tags: string[];
}

export default async function CustomersPage() {
  const customers = await getCustomers();
  const stats = {
    total: customers.length,
    active: customers.filter((c) => c.status === "active").length,
    prospects: customers.filter((c) => c.status === "prospect" || c.status === "lead").length,
    totalRevenue: customers.reduce((sum, c) => sum + c.totalRevenue, 0),
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Customers</h1>
          <p className="page-description">
            Manage customer relationships and track engagement
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
          <Link href="/customers/new">
            <Button className="shadow-glow-sm hover:shadow-glow">
              <Plus className="w-4 h-4 mr-2" />
              Add Customer
            </Button>
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="quick-stats">
        <div className="quick-stat">
          <p className="metric-label">Total Customers</p>
          <p className="metric-value text-2xl">{stats.total}</p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Active</p>
          <p className="metric-value text-2xl text-status-success">{stats.active}</p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Prospects</p>
          <p className="metric-value text-2xl text-status-info">{stats.prospects}</p>
        </div>
        <div className="quick-stat">
          <p className="metric-label">Total Revenue</p>
          <p className="metric-value text-2xl">
            ${(stats.totalRevenue / 100).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Customer Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {customers.map((customer, index) => (
          <CustomerCard key={customer.id} customer={customer} index={index} />
        ))}
      </div>
    </div>
  );
}

function CustomerCard({ customer, index }: { customer: Customer; index: number }) {
  const statusConfig = {
    active: { class: "status-badge--success", label: "Active" },
    churned: { class: "status-badge--error", label: "Churned" },
    prospect: { class: "status-badge--info", label: "Prospect" },
    lead: { class: "status-badge--warning", label: "Lead" },
  };

  const tierConfig = {
    enterprise: { class: "text-highlight", icon: Star },
    professional: { class: "text-accent", icon: TrendingUp },
    starter: { class: "text-text-muted", icon: null },
  };

  const config = statusConfig[customer.status];
  const tier = tierConfig[customer.tier];
  const TierIcon = tier.icon;

  return (
    <div
      className="card card--interactive p-5 animate-fade-up"
      style={{ animationDelay: `${index * 50}ms` }}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-accent/20 to-highlight/20 flex items-center justify-center text-lg font-semibold text-accent">
            {customer.name.charAt(0)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <Link
                href={`/customers/${customer.id}`}
                className="font-semibold text-text-primary hover:text-accent transition-colors"
              >
                {customer.name}
              </Link>
              {TierIcon && <TierIcon className={cn("w-4 h-4", tier.class)} />}
            </div>
            <p className="text-sm text-text-muted">{customer.company}</p>
          </div>
        </div>
        <span className={cn("status-badge", config.class)}>{config.label}</span>
      </div>

      {/* Contact Info */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center gap-2 text-sm text-text-secondary">
          <Mail className="w-4 h-4 text-text-muted" />
          <span className="truncate">{customer.email}</span>
        </div>
        {customer.phone && (
          <div className="flex items-center gap-2 text-sm text-text-secondary">
            <Phone className="w-4 h-4 text-text-muted" />
            <span>{customer.phone}</span>
          </div>
        )}
        {customer.location && (
          <div className="flex items-center gap-2 text-sm text-text-secondary">
            <MapPin className="w-4 h-4 text-text-muted" />
            <span>{customer.location}</span>
          </div>
        )}
      </div>

      {/* Tags */}
      {customer.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {customer.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 text-2xs font-medium rounded-full bg-surface-overlay text-text-muted"
            >
              {tag}
            </span>
          ))}
          {customer.tags.length > 3 && (
            <span className="px-2 py-0.5 text-2xs font-medium rounded-full bg-surface-overlay text-text-muted">
              +{customer.tags.length - 3}
            </span>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-border">
        <div className="flex items-center gap-1 text-sm">
          <DollarSign className="w-4 h-4 text-status-success" />
          <span className="font-semibold text-text-primary tabular-nums">
            ${(customer.totalRevenue / 100).toLocaleString()}
          </span>
        </div>
        <div className="flex items-center gap-1 text-xs text-text-muted">
          <Calendar className="w-3 h-3" />
          Last contact: {new Date(customer.lastContact).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
}

async function getCustomers(): Promise<Customer[]> {
  return [
    {
      id: "cust-1",
      name: "John Smith",
      email: "john.smith@acmecorp.com",
      company: "Acme Corporation",
      phone: "+1 (555) 123-4567",
      location: "San Francisco, CA",
      status: "active",
      tier: "enterprise",
      totalRevenue: 1250000,
      lastContact: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      createdAt: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString(),
      tags: ["VIP", "Annual Contract", "Tech"],
    },
    {
      id: "cust-2",
      name: "Sarah Johnson",
      email: "sarah@techstart.io",
      company: "TechStart Inc",
      phone: "+1 (555) 234-5678",
      location: "Austin, TX",
      status: "active",
      tier: "professional",
      totalRevenue: 450000,
      lastContact: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      createdAt: new Date(Date.now() - 180 * 24 * 60 * 60 * 1000).toISOString(),
      tags: ["Startup", "Fast Growing"],
    },
    {
      id: "cust-3",
      name: "Michael Chen",
      email: "m.chen@globalind.com",
      company: "Global Industries",
      location: "New York, NY",
      status: "active",
      tier: "enterprise",
      totalRevenue: 2100000,
      lastContact: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      createdAt: new Date(Date.now() - 400 * 24 * 60 * 60 * 1000).toISOString(),
      tags: ["VIP", "Multi-year", "Enterprise"],
    },
    {
      id: "cust-4",
      name: "Emily Davis",
      email: "emily@startupxyz.com",
      company: "StartupXYZ",
      phone: "+1 (555) 345-6789",
      status: "prospect",
      tier: "starter",
      totalRevenue: 0,
      lastContact: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      createdAt: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
      tags: ["Trial", "Demo Scheduled"],
    },
    {
      id: "cust-5",
      name: "David Wilson",
      email: "david@creativeagency.co",
      company: "Creative Agency",
      location: "Los Angeles, CA",
      status: "active",
      tier: "professional",
      totalRevenue: 320000,
      lastContact: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      createdAt: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString(),
      tags: ["Marketing", "Agency"],
    },
    {
      id: "cust-6",
      name: "Lisa Anderson",
      email: "lisa@healthcareplus.org",
      company: "HealthCare Plus",
      phone: "+1 (555) 456-7890",
      location: "Chicago, IL",
      status: "lead",
      tier: "enterprise",
      totalRevenue: 0,
      lastContact: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      createdAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      tags: ["Healthcare", "High Priority"],
    },
  ];
}
