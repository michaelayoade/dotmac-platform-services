/**
 * Webhooks API
 *
 * Webhook subscription management, testing, and delivery history
 */

import { api, ApiClientError } from "./client";

// ============================================================================
// Webhook Types
// ============================================================================

export type WebhookEvent = string;

export type DeliveryStatus = "pending" | "success" | "failed" | "retrying" | "disabled";

export interface WebhookSubscription {
  id: string;
  url: string;
  description?: string | null;
  events: WebhookEvent[];
  isActive: boolean;
  retryEnabled: boolean;
  maxRetries: number;
  timeoutSeconds: number;
  successCount: number;
  failureCount: number;
  lastTriggeredAt?: string | null;
  lastSuccessAt?: string | null;
  lastFailureAt?: string | null;
  createdAt: string;
  updatedAt?: string | null;
  customMetadata?: Record<string, unknown>;
  secret?: string;
}

export interface WebhookDelivery {
  id: string;
  subscriptionId: string;
  eventType: string;
  eventId: string;
  status: DeliveryStatus;
  responseCode?: number | null;
  errorMessage?: string | null;
  attemptNumber: number;
  durationMs?: number | null;
  createdAt: string;
  nextRetryAt?: string | null;
}

// ============================================================================
// Webhook Subscription CRUD
// ============================================================================

export interface CreateWebhookData {
  url: string;
  description?: string;
  events: WebhookEvent[];
  headers?: Record<string, string>;
  isActive?: boolean;
  retryEnabled?: boolean;
  maxRetries?: number;
  timeoutSeconds?: number;
  customMetadata?: Record<string, unknown>;
}

export async function getWebhooks(): Promise<WebhookSubscription[]> {
  return api.get<WebhookSubscription[]>("/api/v1/webhooks/subscriptions");
}

export async function getWebhook(id: string): Promise<WebhookSubscription> {
  return api.get<WebhookSubscription>(`/api/v1/webhooks/subscriptions/${id}`);
}

export async function createWebhook(data: CreateWebhookData): Promise<WebhookSubscription> {
  const response = await api.post<WebhookSubscription>("/api/v1/webhooks/subscriptions", {
    url: data.url,
    description: data.description,
    events: data.events,
    headers: data.headers ?? {},
    retryEnabled: data.retryEnabled ?? true,
    maxRetries: data.maxRetries ?? 3,
    timeoutSeconds: data.timeoutSeconds ?? 30,
    customMetadata: data.customMetadata ?? {},
  });

  if (data.isActive === false) {
    return updateWebhook(response.id, { isActive: false });
  }

  return response;
}

export async function updateWebhook(
  id: string,
  data: Partial<CreateWebhookData>
): Promise<WebhookSubscription> {
  return api.patch<WebhookSubscription>(`/api/v1/webhooks/subscriptions/${id}`, {
    url: data.url,
    description: data.description,
    events: data.events,
    headers: data.headers,
    isActive: data.isActive,
    retryEnabled: data.retryEnabled,
    maxRetries: data.maxRetries,
    timeoutSeconds: data.timeoutSeconds,
    customMetadata: data.customMetadata,
  });
}

export async function deleteWebhook(id: string): Promise<void> {
  return api.delete(`/api/v1/webhooks/subscriptions/${id}`);
}

export async function enableWebhook(id: string): Promise<WebhookSubscription> {
  return updateWebhook(id, { isActive: true });
}

export async function disableWebhook(id: string): Promise<WebhookSubscription> {
  return updateWebhook(id, { isActive: false });
}

// ============================================================================
// Webhook Testing
// ============================================================================

export interface WebhookTestResult {
  success: boolean;
  statusCode?: number | null;
  responseBody?: string | null;
  errorMessage?: string | null;
  deliveryTimeMs?: number;
}

export async function testWebhook(webhookId: string): Promise<WebhookTestResult> {
  return api.post<WebhookTestResult>(`/api/v1/webhooks/subscriptions/${webhookId}/test`, {
    eventType: "webhook.test",
  });
}

export async function sendTestEvent(
  webhookId: string,
  eventType: WebhookEvent,
  payload?: Record<string, unknown>
): Promise<WebhookTestResult> {
  return api.post<WebhookTestResult>(`/api/v1/webhooks/subscriptions/${webhookId}/test`, {
    eventType,
    payload,
  });
}

// ============================================================================
// Webhook Deliveries
// ============================================================================

export interface GetDeliveriesParams {
  page?: number;
  pageSize?: number;
  status?: DeliveryStatus;
}

export async function getWebhookDeliveries(
  webhookId: string,
  params: GetDeliveriesParams = {}
): Promise<{
  deliveries: WebhookDelivery[];
  totalCount: number;
  pageCount: number;
}> {
  const { page = 1, pageSize = 50, status } = params;
  const offset = Math.max(page - 1, 0) * pageSize;

  const deliveries = await api.get<WebhookDelivery[]>(
    `/api/v1/webhooks/subscriptions/${webhookId}/deliveries`,
    {
      params: {
        status,
        limit: pageSize,
        offset,
      },
    }
  );

  return {
    deliveries,
    totalCount: deliveries.length,
    pageCount: deliveries.length ? 1 : 0,
  };
}

export async function getWebhookDelivery(
  _webhookId: string,
  deliveryId: string
): Promise<WebhookDelivery> {
  return api.get<WebhookDelivery>(`/api/v1/webhooks/deliveries/${deliveryId}`);
}

export async function retryWebhookDelivery(
  _webhookId: string,
  deliveryId: string
): Promise<WebhookDelivery> {
  await api.post(`/api/v1/webhooks/deliveries/${deliveryId}/retry`);
  return getWebhookDelivery("", deliveryId);
}

// ============================================================================
// Webhook Statistics
// ============================================================================

export interface WebhookStats {
  totalDeliveries: number;
  successfulDeliveries: number;
  failedDeliveries: number;
  pendingDeliveries: number;
}

export async function getWebhookStats(_params?: { periodDays?: number }): Promise<WebhookStats> {
  throw new ApiClientError("Webhook stats are not supported by the backend yet", 501, "NOT_IMPLEMENTED");
}

// ============================================================================
// Available Event Types
// ============================================================================

export interface WebhookEventInfo {
  eventType: string;
  description: string;
  hasSchema: boolean;
  hasExample: boolean;
}

export async function getWebhookEvents(): Promise<WebhookEventInfo[]> {
  const response = await api.get<{ events: WebhookEventInfo[] }>("/api/v1/webhooks/events");
  return response.events;
}

// ============================================================================
// Webhook Secret Management
// ============================================================================

export async function rotateWebhookSecret(webhookId: string): Promise<{ secret: string }> {
  return api.post<{ secret: string }>(
    `/api/v1/webhooks/subscriptions/${webhookId}/rotate-secret`
  );
}
