"use client";

import { use, useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  MessageSquare,
  Send,
  User,
  Clock,
  Tag,
  Link2,
  Trash2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Circle,
  ArrowUp,
  ArrowDown,
  Minus,
  Lock,
  Unlock,
  UserPlus,
  RefreshCcw,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { Button, Card, Input } from "@dotmac/core";
import { useToast } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { ConfirmDialog, useConfirmDialog } from "@/components/shared/confirm-dialog";
import {
  useTicket,
  useTicketMessages,
  useAddTicketMessage,
  useUpdateTicketStatus,
  useAssignTicket,
  useDeleteTicket,
} from "@/lib/hooks/api/use-ticketing";
import type { TicketStatus } from "@/lib/api/ticketing";

interface TicketDetailPageProps {
  params: Promise<{ id: string }>;
}

const statusConfig = {
  open: { label: "Open", color: "bg-status-info/15 text-status-info", icon: Circle },
  in_progress: { label: "In Progress", color: "bg-accent-subtle text-accent", icon: Clock },
  waiting: { label: "Waiting", color: "bg-status-warning/15 text-status-warning", icon: AlertCircle },
  resolved: { label: "Resolved", color: "bg-status-success/15 text-status-success", icon: CheckCircle2 },
  closed: { label: "Closed", color: "bg-surface-overlay text-text-muted", icon: XCircle },
};

const priorityConfig = {
  low: { label: "Low", color: "text-text-muted", icon: ArrowDown },
  normal: { label: "Normal", color: "text-status-info", icon: Minus },
  high: { label: "High", color: "text-status-warning", icon: ArrowUp },
  urgent: { label: "Urgent", color: "text-status-error", icon: AlertCircle },
};

export default function TicketDetailPage({ params }: TicketDetailPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const { toast } = useToast();
  const { confirm, dialog } = useConfirmDialog();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [newMessage, setNewMessage] = useState("");
  const [isInternal, setIsInternal] = useState(false);

  const { data: ticket, isLoading, error } = useTicket(id);
  const { data: messages } = useTicketMessages(id);

  const addMessage = useAddTicketMessage();
  const updateStatus = useUpdateTicketStatus();
  const assignTicket = useAssignTicket();
  const deleteTicket = useDeleteTicket();

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;

    try {
      await addMessage.mutateAsync({
        ticketId: id,
        message: newMessage,
        isInternal,
      });
      setNewMessage("");
      toast({ title: "Message sent" });
    } catch {
      toast({ title: "Failed to send message", variant: "error" });
    }
  };

  const handleStatusChange = async (newStatus: TicketStatus) => {
    try {
      await updateStatus.mutateAsync({ ticketId: id, status: newStatus });
      toast({ title: `Status updated to ${newStatus}` });
    } catch {
      toast({ title: "Failed to update status", variant: "error" });
    }
  };

  const handleDelete = async () => {
    const confirmed = await confirm({
      title: "Delete Ticket",
      description: "Are you sure you want to delete this ticket? This action cannot be undone.",
      variant: "danger",
    });

    if (confirmed) {
      try {
        await deleteTicket.mutateAsync(id);
        toast({ title: "Ticket deleted" });
        router.push("/tickets");
      } catch {
        toast({ title: "Failed to delete ticket", variant: "error" });
      }
    }
  };

  if (isLoading) {
    return <TicketDetailSkeleton />;
  }

  if (error || !ticket) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <MessageSquare className="w-12 h-12 text-text-muted mb-4" />
        <h2 className="text-xl font-semibold text-text-primary mb-2">Ticket not found</h2>
        <p className="text-text-muted mb-6">This ticket doesn&apos;t exist or you don&apos;t have access.</p>
        <Button onClick={() => router.push("/tickets")}>Back to Tickets</Button>
      </div>
    );
  }

  const status = statusConfig[ticket.status as keyof typeof statusConfig] || statusConfig.open;
  const priority = priorityConfig[ticket.priority as keyof typeof priorityConfig] || priorityConfig.normal;
  const StatusIcon = status.icon;
  const PriorityIcon = priority.icon;

  return (
    <div className="space-y-6 animate-fade-up">
      {dialog}

      <PageHeader
        title={ticket.subject}
        breadcrumbs={[
          { label: "Tickets", href: "/tickets" },
          { label: `#${ticket.id.slice(0, 8)}` },
        ]}
        badge={
          <div className="flex items-center gap-2">
            <span className={cn("inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium", status.color)}>
              <StatusIcon className="w-3 h-3" />
              {status.label}
            </span>
            <span className={cn("inline-flex items-center gap-1 text-sm", priority.color)}>
              <PriorityIcon className="w-4 h-4" />
              {priority.label}
            </span>
          </div>
        }
        actions={
          <div className="flex items-center gap-2">
            <select
              value={ticket.status}
              onChange={(e) => handleStatusChange(e.target.value as TicketStatus)}
              className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
            >
              <option value="open">Open</option>
              <option value="in_progress">In Progress</option>
            <option value="waiting">Waiting</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
            <Button variant="destructive" size="sm" onClick={handleDelete}>
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content - Messages */}
        <div className="lg:col-span-2 space-y-4">
          {/* Original ticket */}
          <Card className="p-6">
            <div className="flex items-start gap-4 mb-4">
              <div className="w-10 h-10 rounded-full bg-accent-subtle flex items-center justify-center">
                <User className="w-5 h-5 text-accent" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-text-primary">{ticket.customer?.name || "Tenant"}</span>
                  <span className="text-sm text-text-muted">
                    {formatDistanceToNow(new Date(ticket.createdAt), { addSuffix: true })}
                  </span>
                </div>
                <p className="text-text-secondary whitespace-pre-wrap">{ticket.description}</p>
              </div>
            </div>
          </Card>

          {/* Messages */}
          <Card className="p-0 overflow-hidden">
            <div className="max-h-[500px] overflow-auto p-4 space-y-4">
              {messages && messages.length > 0 ? (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      "flex items-start gap-4 p-4 rounded-lg",
                      message.isInternal ? "bg-status-warning/15" : "bg-surface-overlay"
                    )}
                  >
                    <div
                      className={cn(
                        "w-10 h-10 rounded-full flex items-center justify-center",
                        message.author.type === "agent" ? "bg-accent-subtle" : "bg-surface-overlay"
                      )}
                    >
                      <User
                        className={cn(
                          "w-5 h-5",
                          message.author.type === "agent" ? "text-accent" : "text-text-muted"
                        )}
                      />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-text-primary">
                          {message.author.name ||
                            (message.author.type === "agent"
                              ? "Agent"
                              : message.author.type === "system"
                              ? "System"
                              : ticket.customer?.name || "Tenant")}
                        </span>
                        {message.isInternal && (
                          <span className="flex items-center gap-1 text-xs text-status-warning">
                            <Lock className="w-3 h-3" />
                            Internal
                          </span>
                        )}
                        <span className="text-sm text-text-muted">
                          {format(new Date(message.createdAt), "MMM d, HH:mm")}
                        </span>
                      </div>
                      <p className="text-text-secondary whitespace-pre-wrap">{message.content}</p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-center text-text-muted py-8">No messages yet</p>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Reply form */}
            <div className="border-t border-border-subtle p-4">
              <div className="flex items-center gap-2 mb-3">
                <button
                  onClick={() => setIsInternal(false)}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm transition-colors",
                    !isInternal ? "bg-accent text-text-inverse" : "bg-surface-overlay text-text-muted hover:text-text-secondary"
                  )}
                >
                  <Unlock className="w-4 h-4" />
                  Public Reply
                </button>
                <button
                  onClick={() => setIsInternal(true)}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm transition-colors",
                    isInternal ? "bg-status-warning text-text-inverse" : "bg-surface-overlay text-text-muted hover:text-text-secondary"
                  )}
                >
                  <Lock className="w-4 h-4" />
                  Internal Note
                </button>
              </div>
              <div className="flex items-end gap-3">
                <textarea
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder={isInternal ? "Add an internal note..." : "Type your reply..."}
                  className="flex-1 p-3 bg-surface-primary border border-border-subtle rounded-lg text-sm resize-none min-h-[80px]"
                />
                <Button onClick={handleSendMessage} disabled={!newMessage.trim() || addMessage.isPending}>
                  <Send className="w-4 h-4 mr-2" />
                  {addMessage.isPending ? "Sending..." : "Send"}
                </Button>
              </div>
            </div>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Details */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Details</h3>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-text-muted mb-1">Tenant</p>
                <p className="text-text-primary">{ticket.customer?.name || ticket.customer?.id}</p>
              </div>
              <div>
                <p className="text-sm text-text-muted mb-1">Created</p>
                <p className="text-text-primary">{format(new Date(ticket.createdAt), "MMM d, yyyy 'at' HH:mm")}</p>
              </div>
              <div>
                <p className="text-sm text-text-muted mb-1">Last Updated</p>
                <p className="text-text-primary">{formatDistanceToNow(new Date(ticket.updatedAt), { addSuffix: true })}</p>
              </div>
              <div>
                <p className="text-sm text-text-muted mb-1">Assigned To</p>
                {ticket.assignee ? (
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded-full bg-accent-subtle flex items-center justify-center">
                      <User className="w-3 h-3 text-accent" />
                    </div>
                    <span className="text-text-primary">{ticket.assignee.name || "Agent"}</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <span className="text-text-muted">Unassigned</span>
                    <Button variant="ghost" size="sm">
                      <UserPlus className="w-4 h-4 mr-1" />
                      Assign
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </Card>

          {/* Tags */}
          <Card className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-text-primary">Tags</h3>
              <Button variant="ghost" size="sm">
                <Tag className="w-4 h-4" />
              </Button>
            </div>
            {ticket.tags && ticket.tags.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {ticket.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-sm bg-surface-overlay text-text-secondary"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-muted">No tags</p>
            )}
          </Card>

          {/* Category */}
          {ticket.category && (
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-2">Category</h3>
              <p className="text-text-secondary capitalize">{ticket.category}</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

function TicketDetailSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="h-8 w-96 bg-surface-overlay rounded" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="card p-6 h-40" />
          <div className="card p-6 h-96" />
        </div>
        <div className="space-y-4">
          <div className="card p-6 h-64" />
          <div className="card p-6 h-32" />
        </div>
      </div>
    </div>
  );
}
