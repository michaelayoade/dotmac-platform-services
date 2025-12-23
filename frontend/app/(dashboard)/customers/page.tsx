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
import { DataTable, type ColumnDef } from "@/lib/dotmac/data-table";
import { Button } from "@/lib/dotmac/core";

import { cn } from "@/lib/utils";
import {
  getCustomers as fetchCustomers,
  type Customer as APICustomer,
} from "@/lib/api/customers";

export const metadata = {
  title: "Customers",
  description: "Customer relationship management",
};

// Display interface for CustomerCard component
interface CustomerDisplay {
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

// Map API customer to display format
function mapCustomerToDisplay(customer: APICustomer): CustomerDisplay {
  const typeToTier: Record<string, CustomerDisplay["tier"]> = {
    enterprise: "enterprise",
    business: "professional",
    individual: "starter",
  };

  const statusMap: Record<string, CustomerDisplay["status"]> = {
    active: "active",
    inactive: "prospect",
    churned: "churned",
    lead: "lead",
  };

  return {
    id: customer.id,
    name: customer.name,
    email: customer.email,
    company: customer.company || "",
    phone: customer.phone,
    location: customer.billingAddress
      ? `${customer.billingAddress.city}, ${customer.billingAddress.state}`
      : undefined,
    status: statusMap[customer.status] || "prospect",
    tier: typeToTier[customer.type] || "starter",
    totalRevenue: 0, // Would need separate metrics call for real revenue
    lastContact: customer.updatedAt,
    createdAt: customer.createdAt,
    tags: customer.tags || [],
  };
}

export default async function CustomersPage() {
  const { customers: apiCustomers } = await fetchCustomers({ pageSize: 50 });
  const customers = apiCustomers.map(mapCustomerToDisplay);
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

function CustomerCard({ customer, index }: { customer: CustomerDisplay; index: number }) {
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
