"use client";

import { useState } from "react";
import Link from "next/link";
import {
  MessageSquare,
  Plus,
  Search,
  Filter,
  Clock,
  User,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Circle,
  ArrowUp,
  ArrowDown,
  Minus,
  Tag,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { Button, Card, Input } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useTickets, useTicketStats } from "@/lib/hooks/api/use-ticketing";
import type { Ticket, TicketPriority, TicketStatus } from "@/lib/api/ticketing";

const statusConfig: Record<TicketStatus, { label: string; color: string; icon: React.ElementType }> = {
  open: { label: "Open", color: "bg-status-info/15 text-status-info", icon: Circle },
  in_progress: { label: "In Progress", color: "bg-accent-subtle text-accent", icon: Clock },
  waiting: { label: "Waiting", color: "bg-status-warning/15 text-status-warning", icon: AlertCircle },
  resolved: { label: "Resolved", color: "bg-status-success/15 text-status-success", icon: CheckCircle2 },
  closed: { label: "Closed", color: "bg-surface-overlay text-text-muted", icon: XCircle },
};

const priorityConfig: Record<TicketPriority, { label: string; color: string; icon: React.ElementType }> = {
  low: { label: "Low", color: "text-text-muted", icon: ArrowDown },
  normal: { label: "Normal", color: "text-status-info", icon: Minus },
  high: { label: "High", color: "text-status-warning", icon: ArrowUp },
  urgent: { label: "Urgent", color: "text-status-error", icon: AlertCircle },
};

export default function TicketsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<TicketStatus | "all">("all");
  const [priorityFilter, setPriorityFilter] = useState<TicketPriority | "all">("all");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useTickets({
    page,
    pageSize: 20,
    search: searchQuery || undefined,
    status: statusFilter === "all" ? undefined : statusFilter,
    priority: priorityFilter === "all" ? undefined : priorityFilter,
  });
  const { data: stats } = useTicketStats();

  const tickets: Ticket[] = data?.tickets || [];
  const totalPages = data?.pageCount || 1;
  const statusCounts = stats?.byStatus ?? {
    open: 0,
    in_progress: 0,
    waiting: 0,
    resolved: 0,
    closed: 0,
  };

  if (isLoading) {
    return <TicketsSkeleton />;
  }

  return (
    <div className="space-y-8 animate-fade-up">
      <PageHeader
        title="Tickets"
        description="Manage support tickets and tenant inquiries"
        actions={
          <Link href="/tickets/new">
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              New Ticket
            </Button>
          </Link>
        }
      />

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="p-4">
            <p className="text-sm text-text-muted mb-1">Total Tickets</p>
            <p className="text-2xl font-semibold text-text-primary">{stats.total}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-text-muted mb-1">In Progress</p>
            <p className="text-2xl font-semibold text-accent">{statusCounts.in_progress || 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-text-muted mb-1">Waiting</p>
            <p className="text-2xl font-semibold text-status-warning">{statusCounts.waiting || 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-text-muted mb-1">Resolved</p>
            <p className="text-2xl font-semibold text-status-success">{statusCounts.resolved || 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-text-muted mb-1">Avg Resolution</p>
            <p className="text-2xl font-semibold text-text-primary">
              {stats.avgResolutionTime || "N/A"}
            </p>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search tickets..."
            className="pl-10"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-text-muted" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as TicketStatus | "all")}
            className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
          >
            <option value="all">All Status</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="waiting">Waiting</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
        </div>

        <select
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value as TicketPriority | "all")}
          className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
        >
          <option value="all">All Priority</option>
          <option value="low">Low</option>
          <option value="normal">Normal</option>
          <option value="high">High</option>
          <option value="urgent">Urgent</option>
        </select>
      </div>

      {/* Tickets List */}
      {tickets.length === 0 ? (
        <Card className="p-12 text-center">
          <MessageSquare className="w-12 h-12 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">No tickets found</h3>
          <p className="text-text-muted mb-6">
            {searchQuery || statusFilter !== "all" || priorityFilter !== "all"
              ? "Try adjusting your filters"
              : "Create a new ticket to get started"}
          </p>
          <Link href="/tickets/new">
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              New Ticket
            </Button>
          </Link>
        </Card>
      ) : (
        <Card>
          <div className="divide-y divide-border-subtle">
            {tickets.map((ticket) => {
              const status = statusConfig[ticket.status as TicketStatus] || statusConfig.open;
              const priority = priorityConfig[ticket.priority as TicketPriority] || priorityConfig.normal;
              const StatusIcon = status.icon;
              const PriorityIcon = priority.icon;

              return (
                <Link
                  key={ticket.id}
                  href={`/tickets/${ticket.id}`}
                  className="flex items-start gap-4 p-4 hover:bg-surface-overlay/50 transition-colors"
                >
                  {/* Priority indicator */}
                  <div className="mt-1">
                    <PriorityIcon className={cn("w-5 h-5", priority.color)} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                      <span className="text-sm text-text-muted font-mono">#{ticket.id.slice(0, 8)}</span>
                      <span
                        className={cn(
                          "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium",
                          status.color
                        )}
                      >
                        <StatusIcon className="w-3 h-3" />
                        {status.label}
                      </span>
                    </div>
                    <h4 className="font-medium text-text-primary mb-1 truncate">{ticket.subject}</h4>
                    {ticket.description && (
                      <p className="text-sm text-text-muted line-clamp-1">{ticket.description}</p>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-sm text-text-muted">
                      <span className="flex items-center gap-1">
                        <User className="w-4 h-4" />
                        {ticket.customer?.name || ticket.customer?.id}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {formatDistanceToNow(new Date(ticket.createdAt), { addSuffix: true })}
                      </span>
                      {ticket.tags && ticket.tags.length > 0 && (
                        <span className="flex items-center gap-1">
                          <Tag className="w-4 h-4" />
                          {ticket.tags.length}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Assignee */}
                  <div className="text-right">
                    {ticket.assignee ? (
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-accent-subtle flex items-center justify-center">
                          <User className="w-4 h-4 text-accent" />
                        </div>
                        <span className="text-sm text-text-secondary">{ticket.assignee.name || "Agent"}</span>
                      </div>
                    ) : (
                      <span className="text-sm text-text-muted">Unassigned</span>
                    )}
                  </div>
                </Link>
              );
            })}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-border-subtle">
              <p className="text-sm text-text-muted">
                Page {page} of {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

function TicketsSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="h-8 w-48 bg-surface-overlay rounded" />
      <div className="grid grid-cols-5 gap-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="card p-4 h-20" />
        ))}
      </div>
      <div className="card divide-y divide-border-subtle">
        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <div key={i} className="p-4 h-24" />
        ))}
      </div>
    </div>
  );
}
