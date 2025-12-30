"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Bell,
  Check,
  CheckCheck,
  Trash2,
  AlertCircle,
  Info,
  AlertTriangle,
  Zap,
  ExternalLink,
  Inbox,
  Settings,
} from "lucide-react";

import { PageHeader } from "@/components/shared/page-header";
import { Card, Button, Select, useToast } from "@dotmac/core";
import { Skeleton } from "@/components/shared/loading-skeleton";
import { cn } from "@/lib/utils";
import {
  useNotifications,
  useMarkNotificationAsRead,
  useMarkAllNotificationsAsRead,
  useDeleteNotification,
  type Notification,
} from "@/lib/hooks/api/use-notifications";

type StatusFilter = "all" | "unread" | "read";
type PriorityFilter = "all" | "low" | "medium" | "high" | "urgent";

const priorityConfig: Record<string, { icon: typeof Info; color: string; bgColor: string; label: string }> = {
  low: { icon: Info, color: "text-text-muted", bgColor: "bg-surface-overlay", label: "Low" },
  medium: { icon: Info, color: "text-status-info", bgColor: "bg-status-info/15", label: "Medium" },
  high: { icon: AlertTriangle, color: "text-status-warning", bgColor: "bg-status-warning/15", label: "High" },
  urgent: { icon: Zap, color: "text-status-error", bgColor: "bg-status-error/15", label: "Urgent" },
};

export default function NotificationsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [priorityFilter, setPriorityFilter] = useState<PriorityFilter>("all");

  const { data, isLoading } = useNotifications({
    page,
    pageSize: 20,
    unreadOnly: statusFilter === "unread" ? true : undefined,
    priority: priorityFilter === "all" ? undefined : priorityFilter,
  });

  const markAsReadMutation = useMarkNotificationAsRead();
  const markAllAsReadMutation = useMarkAllNotificationsAsRead();
  const deleteMutation = useDeleteNotification();

  const notifications = data?.notifications ?? [];
  const totalCount = data?.totalCount ?? 0;
  const pageCount = data?.pageCount ?? 1;
  const unreadCount = data?.unreadCount ?? 0;

  const handleMarkAsRead = (id: string) => {
    markAsReadMutation.mutate(id, {
      onSuccess: () => {
        toast({ title: "Notification marked as read" });
      },
    });
  };

  const handleMarkAllAsRead = () => {
    markAllAsReadMutation.mutate(undefined, {
      onSuccess: (result) => {
        toast({ title: `${result.updated} notifications marked as read` });
      },
    });
  };

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id, {
      onSuccess: () => {
        toast({ title: "Notification archived" });
      },
    });
  };

  const getRelativeTime = (timestamp: string) => {
    const now = new Date();
    const date = new Date(timestamp);
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return "Just now";
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Notifications"
        description="View and manage your notifications"
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => router.push("/settings/notifications")}
            >
              <Settings className="w-4 h-4 mr-2" />
              Preferences
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleMarkAllAsRead}
              disabled={markAllAsReadMutation.isPending || unreadCount === 0}
            >
              <CheckCheck className="w-4 h-4 mr-2" />
              Mark All Read
            </Button>
          </div>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-accent/15">
              <Bell className="w-5 h-5 text-accent" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Total Notifications</p>
              <p className="text-2xl font-semibold text-text-primary">{totalCount}</p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-status-warning/15">
              <AlertCircle className="w-5 h-5 text-status-warning" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Unread</p>
              <p className="text-2xl font-semibold text-text-primary">{unreadCount}</p>
            </div>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-status-success/15">
              <Check className="w-5 h-5 text-status-success" />
            </div>
            <div>
              <p className="text-sm text-text-muted">Read</p>
              <p className="text-2xl font-semibold text-text-primary">{totalCount - unreadCount}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex gap-4">
          <Select
            value={statusFilter}
            onValueChange={(val) => setStatusFilter(val as StatusFilter)}
            options={[
              { value: "all", label: "All Status" },
              { value: "unread", label: "Unread" },
              { value: "read", label: "Read" },
            ]}
            placeholder="Status"
            className="w-[140px]"
          />

          <Select
            value={priorityFilter}
            onValueChange={(val) => setPriorityFilter(val as PriorityFilter)}
            options={[
              { value: "all", label: "All Priority" },
              { value: "low", label: "Low" },
              { value: "medium", label: "Medium" },
              { value: "high", label: "High" },
              { value: "urgent", label: "Urgent" },
            ]}
            placeholder="Priority"
            className="w-[140px]"
          />
        </div>
      </Card>

      {/* Notification List */}
      <Card>
        <div className="divide-y divide-border">
          {isLoading ? (
            <>
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="p-4">
                  <div className="flex items-start gap-4">
                    <Skeleton className="w-10 h-10 rounded-lg" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-48" />
                      <Skeleton className="h-3 w-64" />
                    </div>
                  </div>
                </div>
              ))}
            </>
          ) : notifications.length === 0 ? (
            <div className="p-8 text-center text-text-muted">
              <Inbox className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p className="font-medium">No notifications</p>
              <p className="text-sm">You&apos;re all caught up!</p>
            </div>
          ) : (
            notifications.map((notification) => (
              <NotificationRow
                key={notification.id}
                notification={notification}
                getRelativeTime={getRelativeTime}
                onMarkAsRead={handleMarkAsRead}
                onDelete={handleDelete}
              />
            ))
          )}
        </div>

        {/* Pagination */}
        {pageCount > 1 && (
          <div className="flex items-center justify-between p-4 border-t border-border">
            <p className="text-sm text-text-muted">
              Page {page} of {pageCount}
            </p>
            <div className="flex gap-2">
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
                onClick={() => setPage((p) => Math.min(pageCount, p + 1))}
                disabled={page === pageCount}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

function NotificationRow({
  notification,
  getRelativeTime,
  onMarkAsRead,
  onDelete,
}: {
  notification: Notification;
  getRelativeTime: (ts: string) => string;
  onMarkAsRead: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  const priority = priorityConfig[notification.priority] ?? priorityConfig.medium;
  const PriorityIcon = priority.icon;

  return (
    <div
      className={cn(
        "p-4 transition-colors",
        !notification.isRead && "bg-accent/5"
      )}
    >
      <div className="flex items-start gap-4">
        <div className={cn("p-2 rounded-lg", priority.bgColor)}>
          <PriorityIcon className={cn("w-5 h-5", priority.color)} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <p
              className={cn(
                "text-sm font-medium",
                notification.isRead ? "text-text-secondary" : "text-text-primary"
              )}
            >
              {notification.title}
            </p>
            {!notification.isRead && (
              <span className="w-2 h-2 rounded-full bg-accent" />
            )}
          </div>
          <p className="text-sm text-text-muted mb-2">{notification.message}</p>
          <div className="flex items-center gap-4 text-xs text-text-muted">
            <span>{getRelativeTime(notification.createdAt)}</span>
            <span
              className={cn(
                "px-2 py-0.5 rounded-full text-2xs font-medium",
                priority.bgColor,
                priority.color
              )}
            >
              {priority.label}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1">
          {notification.actionUrl && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => window.open(notification.actionUrl!, "_blank")}
              className="text-text-muted hover:text-text-primary"
            >
              <ExternalLink className="w-4 h-4" />
            </Button>
          )}
          {!notification.isRead && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onMarkAsRead(notification.id)}
              className="text-text-muted hover:text-accent"
            >
              <Check className="w-4 h-4" />
            </Button>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onDelete(notification.id)}
            className="text-text-muted hover:text-status-error"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
