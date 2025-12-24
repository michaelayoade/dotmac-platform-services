/**
 * Communications API
 *
 * Email sending, templates, bulk campaigns, and communication logs
 */

import { api, ApiClientError, normalizePaginatedResponse } from "./client";

// ============================================================================
// Email Types
// ============================================================================

export interface EmailRequest {
  to: string | string[];
  subject: string;
  textBody?: string;
  htmlBody?: string;
  cc?: string[];
  bcc?: string[];
  fromEmail?: string;
  fromName?: string;
  replyTo?: string;
  headers?: Record<string, string>;
  attachments?: Array<{
    filename: string;
    content: string;
    contentType: string;
  }>;
}

export type EmailStatus = "queued" | "sent" | "failed";

export interface EmailResponse {
  id: string;
  messageId: string;
  status: EmailStatus | string;
  accepted: string[];
  rejected: string[];
  queuedAt?: string | null;
  sentAt?: string | null;
}

export interface EmailQueueResponse {
  taskId: string;
  jobId: string;
  status: string;
  queuedAt?: string;
  estimatedSendTime?: string | null;
  message?: string;
}

// ============================================================================
// Email Sending
// ============================================================================

export async function sendEmail(request: EmailRequest): Promise<EmailResponse> {
  return api.post<EmailResponse>("/api/v1/communications/email/send", request);
}

export async function queueEmail(request: EmailRequest): Promise<EmailQueueResponse> {
  return api.post<EmailQueueResponse>("/api/v1/communications/email/queue", request);
}

export async function sendBulkEmails(data: {
  recipients: Array<{ email: string; variables?: Record<string, unknown> }>;
  templateId: string;
  subjectOverride?: string;
  metadata?: Record<string, unknown>;
}): Promise<BulkEmailJob> {
  return queueBulkEmail({
    recipients: data.recipients,
    templateId: data.templateId,
    subjectOverride: data.subjectOverride,
    metadata: data.metadata,
  });
}

// ============================================================================
// Email Templates
// ============================================================================

export interface EmailTemplate {
  id: string;
  name: string;
  description?: string | null;
  channel?: string | null;
  subject?: string | null;
  subjectTemplate?: string | null;
  bodyHtml?: string | null;
  bodyText?: string | null;
  variables: Array<Record<string, unknown>> | string[];
  metadata?: Record<string, unknown>;
  isActive: boolean;
  usageCount: number;
  lastUsedAt?: string | null;
  createdAt: string;
  updatedAt?: string | null;
  tenantId?: string | null;
  createdBy?: string | null;
}

export interface GetTemplatesParams {
  page?: number;
  pageSize?: number;
  search?: string;
  channel?: string;
  isActive?: boolean;
}

export async function getEmailTemplates(params: GetTemplatesParams = {}): Promise<{
  templates: EmailTemplate[];
  totalCount: number;
  pageCount: number;
}> {
  const { page = 1, pageSize = 20, search, channel, isActive } = params;

  const response = await api.get<unknown>("/api/v1/communications/templates", {
    params: {
      page,
      pageSize,
      search,
      channel,
      isActive,
    },
  });
  const normalized = normalizePaginatedResponse<EmailTemplate>(response);

  return {
    templates: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getEmailTemplate(id: string): Promise<EmailTemplate> {
  return api.get<EmailTemplate>(`/api/v1/communications/templates/${id}`);
}

export interface CreateEmailTemplateData {
  name: string;
  description?: string;
  channel?: string;
  subject?: string;
  subjectTemplate?: string;
  bodyHtml?: string;
  bodyText?: string;
  variables?: Array<Record<string, unknown>> | string[];
  metadata?: Record<string, unknown>;
  isActive?: boolean;
}

export async function createEmailTemplate(data: CreateEmailTemplateData): Promise<EmailTemplate> {
  return api.post<EmailTemplate>("/api/v1/communications/templates", data);
}

export async function updateEmailTemplate(
  id: string,
  data: Partial<CreateEmailTemplateData>
): Promise<EmailTemplate> {
  return api.patch<EmailTemplate>(`/api/v1/communications/templates/${id}`, data);
}

export async function deleteEmailTemplate(id: string): Promise<void> {
  return api.delete(`/api/v1/communications/templates/${id}`);
}

export async function previewEmailTemplate(
  templateId: string,
  variables?: Record<string, unknown>
): Promise<{ subject?: string; bodyHtml?: string; bodyText?: string }> {
  return api.post(`/api/v1/communications/templates/${templateId}/render`, {
    variables,
  });
}

export async function testEmailTemplate(
  templateId: string,
  testEmail: string,
  variables?: Record<string, unknown>
): Promise<EmailResponse> {
  const rendered = await previewEmailTemplate(templateId, variables);
  if (!rendered.subject) {
    throw new ApiClientError("Template preview did not return a subject", 400, "INVALID_TEMPLATE");
  }
  return sendEmail({
    to: testEmail,
    subject: rendered.subject,
    htmlBody: rendered.bodyHtml,
    textBody: rendered.bodyText,
  });
}

// ============================================================================
// Bulk Email
// ============================================================================

export interface BulkEmailJob {
  id: string;
  taskId?: string | null;
  tenantId?: string | null;
  templateId?: string | null;
  recipientCount: number;
  status: string;
  progress?: number | null;
  sentCount?: number;
  failedCount?: number;
  pendingCount?: number;
  startedAt?: string | null;
  completedAt?: string | null;
  cancelledAt?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
  metadata?: Record<string, unknown>;
}

export async function queueBulkEmail(data: {
  recipients: Array<{ email: string; variables?: Record<string, unknown> }>;
  templateId: string;
  subjectOverride?: string;
  metadata?: Record<string, unknown>;
}): Promise<BulkEmailJob> {
  return api.post<BulkEmailJob>("/api/v1/communications/bulk/queue", {
    recipients: data.recipients,
    templateId: data.templateId,
    subjectOverride: data.subjectOverride,
    metadata: data.metadata,
  });
}

export async function getBulkEmailJob(jobId: string): Promise<BulkEmailJob> {
  const response = await api.get<{ operation: BulkEmailJob }>(
    `/api/v1/communications/bulk/${jobId}/status`
  );
  return response.operation;
}

export async function cancelBulkEmailJob(jobId: string): Promise<BulkEmailJob> {
  return api.post<BulkEmailJob>(`/api/v1/communications/bulk/${jobId}/cancel`);
}

// ============================================================================
// Communication Logs
// ============================================================================

export type CommunicationChannel = "email" | "sms" | "webhook" | "push";
export type CommunicationStatus = "pending" | "sent" | "delivered" | "failed" | "bounced";

export interface EmailLog {
  id: string;
  tenantId?: string | null;
  channel: CommunicationChannel;
  recipientEmail?: string | null;
  recipientPhone?: string | null;
  recipientName?: string | null;
  subject?: string | null;
  bodyText?: string | null;
  bodyHtml?: string | null;
  templateId?: string | null;
  status: CommunicationStatus | string;
  sentAt?: string | null;
  deliveredAt?: string | null;
  openedAt?: string | null;
  clickedAt?: string | null;
  failedAt?: string | null;
  errorMessage?: string | null;
  metadata?: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

export interface GetEmailLogsParams {
  page?: number;
  pageSize?: number;
  channel?: CommunicationChannel;
  status?: CommunicationStatus;
  recipientEmail?: string;
  templateId?: string;
  startDate?: string;
  endDate?: string;
}

export async function getEmailLogs(params: GetEmailLogsParams = {}): Promise<{
  logs: EmailLog[];
  totalCount: number;
  pageCount: number;
}> {
  const {
    page = 1,
    pageSize = 50,
    channel,
    status,
    recipientEmail,
    templateId,
    startDate,
    endDate,
  } = params;

  const response = await api.get<unknown>("/api/v1/communications/logs", {
    params: {
      page,
      pageSize,
      channel,
      status,
      recipientEmail,
      templateId,
      dateFrom: startDate,
      dateTo: endDate,
    },
  });
  const normalized = normalizePaginatedResponse<EmailLog>(response);

  return {
    logs: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getEmailLog(id: string): Promise<EmailLog> {
  return api.get<EmailLog>(`/api/v1/communications/logs/${id}`);
}

export async function resendEmail(logId: string): Promise<{ logId: string; status: string }> {
  const response = await api.post<{ logId: string; status: string }>(
    `/api/v1/communications/logs/${logId}/retry`
  );
  return response;
}

// ============================================================================
// Communication Statistics
// ============================================================================

export interface CommunicationStats {
  totalSent: number;
  totalDelivered: number;
  totalFailed: number;
  totalBounced: number;
  totalPending: number;
  deliveryRate: number;
  failureRate: number;
  bounceRate: number;
  emailsSent: number;
  smsSent: number;
  webhooksSent: number;
  pushSent: number;
  openRate: number;
  clickRate: number;
  period: string;
  timestamp: string;
  // Additional stats for UI
  sentLast24h: number;
  deliveredLast24h: number;
  failedLast24h: number;
}

export async function getCommunicationStats(params?: {
  periodDays?: number;
}): Promise<CommunicationStats> {
  return api.get<CommunicationStats>("/api/v1/communications/stats", {
    params: {
      periodDays: params?.periodDays,
    },
  });
}
