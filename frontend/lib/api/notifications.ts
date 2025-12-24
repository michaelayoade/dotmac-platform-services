/**
 * Notifications API
 *
 * User notifications, preferences, and team notifications
 */

import { api, ApiClientError } from "./client";

// ============================================================================
// Notification Types
// ============================================================================

export type NotificationType =
  | "customer_activated"
  | "customer_deactivated"
  | "customer_suspended"
  | "customer_reactivated"
  | "service_activated"
  | "service_failed"
  | "service_outage"
  | "service_restored"
  | "bandwidth_limit_reached"
  | "connection_quality_degraded"
  | "alarm"
  | "invoice_generated"
  | "invoice_due"
  | "invoice_overdue"
  | "payment_received"
  | "payment_failed"
  | "subscription_renewed"
  | "subscription_cancelled"
  | "dunning_reminder"
  | "dunning_suspension_warning"
  | "dunning_final_notice"
  | "lead_assigned"
  | "quote_sent"
  | "quote_accepted"
  | "quote_rejected"
  | "site_survey_scheduled"
  | "site_survey_completed"
  | "ticket_created"
  | "ticket_assigned"
  | "ticket_updated"
  | "ticket_resolved"
  | "ticket_closed"
  | "ticket_reopened"
  | "password_reset"
  | "account_locked"
  | "two_factor_enabled"
  | "api_key_expiring"
  | "system_alert"
  | "system_announcement"
  | "custom"
  | string;

export type NotificationPriority = "low" | "medium" | "high" | "urgent";
export type NotificationStatus = "unread" | "read" | "archived";
export type NotificationChannel = "in_app" | "email" | "sms" | "push" | "webhook";

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  priority: NotificationPriority;
  status: NotificationStatus;
  actionUrl?: string | null;
  actionLabel?: string | null;
  relatedEntityType?: string | null;
  relatedEntityId?: string | null;
  channels: NotificationChannel[];
  isRead: boolean;
  readAt?: string | null;
  isArchived: boolean;
  archivedAt?: string | null;
  metadata?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

interface NotificationResponse {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  priority: NotificationPriority;
  actionUrl?: string | null;
  actionLabel?: string | null;
  relatedEntityType?: string | null;
  relatedEntityId?: string | null;
  channels: NotificationChannel[];
  isRead: boolean;
  readAt?: string | null;
  isArchived: boolean;
  archivedAt?: string | null;
  notificationMetadata?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

function toNotification(item: NotificationResponse): Notification {
  const status: NotificationStatus = item.isArchived
    ? "archived"
    : item.isRead
    ? "read"
    : "unread";

  return {
    id: item.id,
    type: item.type,
    title: item.title,
    message: item.message,
    priority: item.priority,
    status,
    actionUrl: item.actionUrl,
    actionLabel: item.actionLabel,
    relatedEntityType: item.relatedEntityType,
    relatedEntityId: item.relatedEntityId,
    channels: item.channels ?? [],
    isRead: item.isRead,
    readAt: item.readAt,
    isArchived: item.isArchived,
    archivedAt: item.archivedAt,
    metadata: item.notificationMetadata,
    createdAt: item.createdAt,
    updatedAt: item.updatedAt,
  };
}

// ============================================================================
// Notification CRUD
// ============================================================================

export interface GetNotificationsParams {
  page?: number;
  pageSize?: number;
  status?: NotificationStatus;
  type?: NotificationType;
  priority?: NotificationPriority;
  unreadOnly?: boolean;
}

export async function getNotifications(params: GetNotificationsParams = {}): Promise<{
  notifications: Notification[];
  totalCount: number;
  pageCount: number;
  unreadCount: number;
}> {
  const { page = 1, pageSize = 50, status, type, priority, unreadOnly } = params;
  const offset = Math.max(page - 1, 0) * pageSize;
  const resolvedUnreadOnly = unreadOnly ?? (status === "unread" ? true : undefined);

  const response = await api.get<{
    notifications: NotificationResponse[];
    total: number;
    unreadCount: number;
  }>("/api/v1/notifications", {
    params: {
      offset,
      limit: pageSize,
      unreadOnly: resolvedUnreadOnly,
      notificationType: type,
      priority,
    },
  });

  return {
    notifications: response.notifications.map(toNotification),
    totalCount: response.total,
    pageCount: pageSize ? Math.ceil(response.total / pageSize) : 0,
    unreadCount: response.unreadCount,
  };
}

export async function getNotification(notificationId: string): Promise<Notification> {
  const response = await getNotifications({ page: 1, pageSize: 100 });
  const match = response.notifications.find((item) => item.id === notificationId);
  if (!match) {
    throw new ApiClientError("Notification not found", 404, "NOT_FOUND");
  }
  return match;
}

export async function getUnreadCount(): Promise<{ count: number }> {
  const response = await api.get<{ unreadCount: number }>("/api/v1/notifications/unread-count");
  return { count: response.unreadCount };
}

export interface CreateNotificationData {
  userId: string;
  type: NotificationType;
  title: string;
  message: string;
  priority?: NotificationPriority;
  actionUrl?: string;
  actionLabel?: string;
  relatedEntityType?: string;
  relatedEntityId?: string;
  channels?: NotificationChannel[];
  metadata?: Record<string, unknown>;
}

export async function createNotification(data: CreateNotificationData): Promise<Notification> {
  const response = await api.post<NotificationResponse>("/api/v1/notifications", {
    userId: data.userId,
    type: data.type,
    title: data.title,
    message: data.message,
    priority: data.priority ?? "medium",
    actionUrl: data.actionUrl,
    actionLabel: data.actionLabel,
    relatedEntityType: data.relatedEntityType,
    relatedEntityId: data.relatedEntityId,
    channels: data.channels,
    metadata: data.metadata,
  });
  return toNotification(response);
}

export async function createNotificationFromTemplate(data: {
  userId: string;
  type: NotificationType;
  variables?: Record<string, unknown>;
}): Promise<Notification> {
  const response = await api.post<NotificationResponse>("/api/v1/notifications/from-template", {
    userId: data.userId,
    type: data.type,
    variables: data.variables,
  });
  return toNotification(response);
}

// ============================================================================
// Notification Actions
// ============================================================================

export async function markAsRead(notificationId: string): Promise<Notification> {
  const response = await api.post<NotificationResponse>(
    `/api/v1/notifications/${notificationId}/read`
  );
  return toNotification(response);
}

export async function markAllAsRead(): Promise<{ updated: number }> {
  const response = await api.post<{ markedRead: number }>("/api/v1/notifications/read-all");
  return { updated: response.markedRead };
}

export async function archiveNotification(notificationId: string): Promise<Notification> {
  const response = await api.post<NotificationResponse>(
    `/api/v1/notifications/${notificationId}/archive`
  );
  return toNotification(response);
}

export async function deleteNotification(notificationId: string): Promise<void> {
  await archiveNotification(notificationId);
}

// ============================================================================
// Notification Preferences
// ============================================================================

export interface NotificationPreferences {
  enabled: boolean;
  emailEnabled: boolean;
  smsEnabled: boolean;
  pushEnabled: boolean;
  quietHoursEnabled: boolean;
  quietHoursStart?: string | null;
  quietHoursEnd?: string | null;
  quietHoursTimezone?: string | null;
  typePreferences?: Record<string, unknown>;
  minimumPriority: NotificationPriority;
  emailDigestEnabled?: boolean;
  emailDigestFrequency?: string | null;
}

export async function getNotificationPreferences(): Promise<NotificationPreferences> {
  return api.get<NotificationPreferences>("/api/v1/notifications/preferences");
}

export async function updateNotificationPreferences(
  preferences: Partial<NotificationPreferences>
): Promise<NotificationPreferences> {
  return api.put<NotificationPreferences>("/api/v1/notifications/preferences", preferences);
}

// ============================================================================
// Team Notifications
// ============================================================================

export async function sendTeamNotification(data: {
  teamMembers?: string[];
  roleFilter?: string;
  notificationType?: NotificationType;
  title: string;
  message: string;
  priority?: NotificationPriority;
  actionUrl?: string;
  actionLabel?: string;
  relatedEntityType?: string;
  relatedEntityId?: string;
  metadata?: Record<string, unknown>;
  autoSend?: boolean;
}): Promise<{
  notificationsCreated: number;
  targetCount: number;
  teamMembers?: string[];
  roleFilter?: string;
  notificationType: string;
  priority: string;
}> {
  return api.post("/api/v1/notifications/team", data);
}

// ============================================================================
// Notification Statistics
// ============================================================================

export interface NotificationStats {
  total: number;
  unread: number;
  read: number;
  byPriority: Record<NotificationPriority, number>;
  topTypes: Record<string, number>;
}

export async function getNotificationStats(): Promise<NotificationStats> {
  return api.get<NotificationStats>("/api/v1/notifications/stats");
}
