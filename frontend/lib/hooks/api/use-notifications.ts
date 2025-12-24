"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getNotifications,
  getNotification,
  markAsRead,
  markAllAsRead,
  deleteNotification,
  getUnreadCount,
  getNotificationPreferences,
  updateNotificationPreferences,
  sendTeamNotification,
  type GetNotificationsParams,
  type Notification,
  type NotificationPreferences,
} from "@/lib/api/notifications";
import { queryKeys } from "@/lib/api/query-keys";

// ============================================================================
// Notifications Hooks
// ============================================================================

export function useNotifications(params?: GetNotificationsParams) {
  return useQuery({
    queryKey: queryKeys.notifications.list(params),
    queryFn: () => getNotifications(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useNotification(id: string) {
  return useQuery({
    queryKey: queryKeys.notifications.detail(id),
    queryFn: () => getNotification(id),
    enabled: !!id,
  });
}

export function useMarkNotificationAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: markAsRead,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.notifications.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.all,
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.count(),
      });
    },
  });
}

export function useMarkAllNotificationsAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: markAllAsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.all,
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.count(),
      });
    },
  });
}

export function useDeleteNotification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteNotification,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.all,
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.notifications.count(),
      });
    },
  });
}

// ============================================================================
// Unread Count Hook
// ============================================================================

export function useUnreadNotificationsCount() {
  return useQuery({
    queryKey: queryKeys.notifications.count(),
    queryFn: getUnreadCount,
    refetchInterval: 30 * 1000, // Poll every 30 seconds
    staleTime: 10 * 1000,
  });
}

// ============================================================================
// Notification Preferences Hooks
// ============================================================================

export function useNotificationPreferences() {
  return useQuery({
    queryKey: queryKeys.notifications.preferences(),
    queryFn: getNotificationPreferences,
  });
}

export function useUpdateNotificationPreferences() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateNotificationPreferences,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.notifications.preferences(), data);
    },
  });
}

// ============================================================================
// Team Notification Hook
// ============================================================================

export function useSendTeamNotification() {
  return useMutation({
    mutationFn: sendTeamNotification,
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  GetNotificationsParams,
  Notification,
  NotificationPreferences,
};
