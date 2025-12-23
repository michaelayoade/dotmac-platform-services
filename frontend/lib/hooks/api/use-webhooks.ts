"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getWebhooks,
  getWebhook,
  createWebhook,
  updateWebhook,
  deleteWebhook,
  enableWebhook,
  disableWebhook,
  testWebhook,
  getWebhookDeliveries,
  getWebhookDelivery,
  retryWebhookDelivery,
  rotateWebhookSecret,
  getWebhookEvents,
  getWebhookStats,
  type WebhookSubscription,
  type CreateWebhookData,
  type WebhookTestResult,
  type GetDeliveriesParams,
  type WebhookDelivery,
  type WebhookEventInfo,
  type WebhookStats,
} from "@/lib/api/webhooks";
import { queryKeys } from "@/lib/api/query-keys";

// ============================================================================
// Webhooks Hooks
// ============================================================================

export function useWebhooks() {
  return useQuery({
    queryKey: queryKeys.webhooks.all(),
    queryFn: getWebhooks,
  });
}

export function useWebhook(id: string) {
  return useQuery({
    queryKey: queryKeys.webhooks.detail(id),
    queryFn: () => getWebhook(id),
    enabled: !!id,
  });
}

export function useCreateWebhook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createWebhook,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.webhooks.all(),
      });
    },
  });
}

export function useUpdateWebhook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateWebhookData> }) =>
      updateWebhook(id, data),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.webhooks.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.webhooks.all(),
      });
    },
  });
}

export function useDeleteWebhook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteWebhook,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.webhooks.all(),
      });
    },
  });
}

export function useEnableWebhook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: enableWebhook,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.webhooks.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.webhooks.all(),
      });
    },
  });
}

export function useDisableWebhook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: disableWebhook,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.webhooks.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.webhooks.all(),
      });
    },
  });
}

export function useTestWebhook() {
  return useMutation({
    mutationFn: testWebhook,
  });
}

export function useRotateWebhookSecret() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: rotateWebhookSecret,
    onSuccess: (_, webhookId) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.webhooks.detail(webhookId),
      });
    },
  });
}

// ============================================================================
// Webhook Deliveries Hooks
// ============================================================================

export function useWebhookDeliveries(webhookId: string, params?: GetDeliveriesParams) {
  return useQuery({
    queryKey: queryKeys.webhooks.deliveries.list(webhookId, params),
    queryFn: () => getWebhookDeliveries(webhookId, params),
    enabled: !!webhookId,
    placeholderData: (previousData) => previousData,
  });
}

export function useWebhookDelivery(webhookId: string, deliveryId: string) {
  return useQuery({
    queryKey: queryKeys.webhooks.deliveries.detail(webhookId, deliveryId),
    queryFn: () => getWebhookDelivery(webhookId, deliveryId),
    enabled: !!webhookId && !!deliveryId,
  });
}

export function useRetryWebhookDelivery() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ webhookId, deliveryId }: { webhookId: string; deliveryId: string }) =>
      retryWebhookDelivery(webhookId, deliveryId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.webhooks.deliveries.all(variables.webhookId),
      });
    },
  });
}

// ============================================================================
// Webhook Events Hook
// ============================================================================

export function useWebhookEvents() {
  return useQuery({
    queryKey: queryKeys.webhooks.events(),
    queryFn: getWebhookEvents,
    staleTime: 60 * 60 * 1000, // 1 hour - events rarely change
  });
}

// ============================================================================
// Webhook Stats Hook
// ============================================================================

export function useWebhookStats(params?: { periodDays?: number }) {
  return useQuery({
    queryKey: queryKeys.webhooks.stats(params),
    queryFn: () => getWebhookStats(params),
    staleTime: 2 * 60 * 1000,
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  WebhookSubscription,
  CreateWebhookData,
  WebhookTestResult,
  GetDeliveriesParams,
  WebhookDelivery,
  WebhookEventInfo,
  WebhookStats,
};
