/**
 * Alerts API
 *
 * Alert channel management and webhook configuration
 */

import { api, ApiClientError } from "./client";

// ============================================================================
// Alert Channel Types
// ============================================================================

export type ChannelType = "slack" | "discord" | "teams" | "webhook" | "email" | "sms";
export type AlertSeverity = "info" | "warning" | "critical";

export interface AlertChannel {
  id: string;
  name: string;
  channelType: ChannelType;
  enabled: boolean;
  tenantId?: string | null;
  severities?: AlertSeverity[] | null;
  alertNames?: string[] | null;
  alertCategories?: string[] | null;
}

export interface AlertChannelPayload {
  id: string;
  name: string;
  channelType: ChannelType;
  webhookUrl: string;
  enabled?: boolean;
  tenantId?: string;
  severities?: AlertSeverity[];
  alertNames?: string[];
  alertCategories?: string[];
  slackChannel?: string;
  slackUsername?: string;
  slackIconEmoji?: string;
  discordUsername?: string;
  discordAvatarUrl?: string;
  teamsTitle?: string;
  customHeaders?: Record<string, string>;
  customPayloadTemplate?: string;
}

export type CreateAlertChannelData = AlertChannelPayload;
export type UpdateAlertChannelData = AlertChannelPayload;

// ============================================================================
// Alert Channel CRUD
// ============================================================================

export async function getAlertChannels(): Promise<AlertChannel[]> {
  return api.get<AlertChannel[]>("/api/v1/monitoring/alerts/channels");
}

export async function getAlertChannel(id: string): Promise<AlertChannel> {
  return api.get<AlertChannel>(`/api/v1/monitoring/alerts/channels/${id}`);
}

export async function createAlertChannel(data: AlertChannelPayload): Promise<AlertChannel> {
  return api.post<AlertChannel>("/api/v1/monitoring/alerts/channels", {
    id: data.id,
    name: data.name,
    channelType: data.channelType,
    webhookUrl: data.webhookUrl,
    enabled: data.enabled ?? true,
    tenantId: data.tenantId,
    severities: data.severities,
    alertNames: data.alertNames,
    alertCategories: data.alertCategories,
    slackChannel: data.slackChannel,
    slackUsername: data.slackUsername,
    slackIconEmoji: data.slackIconEmoji,
    discordUsername: data.discordUsername,
    discordAvatarUrl: data.discordAvatarUrl,
    teamsTitle: data.teamsTitle,
    customHeaders: data.customHeaders,
    customPayloadTemplate: data.customPayloadTemplate,
  });
}

export async function updateAlertChannel(
  id: string,
  data: AlertChannelPayload
): Promise<AlertChannel> {
  return api.patch<AlertChannel>(`/api/v1/monitoring/alerts/channels/${id}`, {
    ...data,
    id,
  });
}

export async function deleteAlertChannel(id: string): Promise<void> {
  return api.delete(`/api/v1/monitoring/alerts/channels/${id}`);
}

export async function enableAlertChannel(payload: AlertChannelPayload): Promise<AlertChannel> {
  return updateAlertChannel(payload.id, { ...payload, enabled: true });
}

export async function disableAlertChannel(payload: AlertChannelPayload): Promise<AlertChannel> {
  return updateAlertChannel(payload.id, { ...payload, enabled: false });
}

// ============================================================================
// Alert Testing
// ============================================================================

export type AlertTestResult = Record<string, boolean>;

export async function testAlertChannel(channelId: string): Promise<AlertTestResult> {
  return sendTestAlert({ channelId });
}

export async function sendTestAlert(params: {
  channelId: string;
  severity?: AlertSeverity;
  message?: string;
}): Promise<AlertTestResult> {
  return api.post<AlertTestResult>("/api/v1/monitoring/alerts/test", {
    channelId: params.channelId,
    severity: params.severity ?? "warning",
    message: params.message,
  });
}

// ============================================================================
// Webhook Processing
// ============================================================================

export interface WebhookProcessingResult {
  alertsProcessed: number;
  totalChannelsNotified: number;
  results: Record<string, Record<string, boolean>>;
}

export async function processAlertWebhook(payload: unknown): Promise<WebhookProcessingResult> {
  return api.post<WebhookProcessingResult>("/api/v1/monitoring/alerts/webhook", payload, {
    transformRequest: false,
  });
}

// ============================================================================
// Alert Rules (backend not yet available)
// ============================================================================

export interface AlertRule {
  id: string;
  name: string;
  description?: string;
  enabled: boolean;
  condition: {
    metric: string;
    operator: "gt" | "lt" | "eq" | "gte" | "lte";
    threshold: number;
    duration?: string;
  };
  severity: AlertSeverity;
  channels: string[];
  labels?: Record<string, string>;
  annotations?: Record<string, string>;
  createdAt: string;
  updatedAt: string;
}

export interface CreateAlertRuleData {
  name: string;
  description?: string;
  enabled?: boolean;
  condition: AlertRule["condition"];
  severity: AlertSeverity;
  channels: string[];
  labels?: Record<string, string>;
  annotations?: Record<string, string>;
}

function unsupportedAlertsFeature(feature: string): never {
  throw new ApiClientError(
    `${feature} is not supported by the backend yet`,
    501,
    "NOT_IMPLEMENTED"
  );
}

export async function getAlertRules(): Promise<AlertRule[]> {
  return unsupportedAlertsFeature("Alert rules");
}

export async function getAlertRule(_id: string): Promise<AlertRule> {
  return unsupportedAlertsFeature("Alert rules");
}

export async function createAlertRule(_data: CreateAlertRuleData): Promise<AlertRule> {
  return unsupportedAlertsFeature("Alert rules");
}

export async function updateAlertRule(
  _id: string,
  _data: Partial<CreateAlertRuleData>
): Promise<AlertRule> {
  return unsupportedAlertsFeature("Alert rules");
}

export async function deleteAlertRule(_id: string): Promise<void> {
  return unsupportedAlertsFeature("Alert rules");
}

export async function enableAlertRule(_id: string): Promise<AlertRule> {
  return unsupportedAlertsFeature("Alert rules");
}

export async function disableAlertRule(_id: string): Promise<AlertRule> {
  return unsupportedAlertsFeature("Alert rules");
}

// ============================================================================
// Alert History (backend not yet available)
// ============================================================================

export interface AlertHistoryParams {
  page?: number;
  pageSize?: number;
  status?: "firing" | "resolved";
  severity?: AlertSeverity;
}

export interface AlertEvent {
  id: string;
  status: "firing" | "resolved";
  alertName: string;
  message: string;
  severity: AlertSeverity;
  createdAt: string;
}

export interface AlertStats {
  total: number;
  firing: number;
  resolved: number;
  bySeverity: Record<AlertSeverity, number>;
}

export async function getAlertHistory(_params?: AlertHistoryParams): Promise<{
  events: AlertEvent[];
  totalCount: number;
  pageCount: number;
}> {
  return unsupportedAlertsFeature("Alert history");
}

export async function acknowledgeAlert(_alertId: string, _note?: string): Promise<void> {
  return unsupportedAlertsFeature("Alert history");
}

export async function resolveAlert(_alertId: string, _resolution?: string): Promise<void> {
  return unsupportedAlertsFeature("Alert history");
}

export async function getAlertStats(_params?: { periodDays?: number }): Promise<AlertStats> {
  return unsupportedAlertsFeature("Alert stats");
}
