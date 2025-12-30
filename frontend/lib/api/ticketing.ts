/**
 * Ticketing API
 *
 * Support ticket management, messaging, and agent assignment
 */

import { api, normalizePaginatedResponse, ApiClientError } from "./client";
import type { TicketsDashboardResponse, DashboardQueryParams } from "./types/dashboard";

// ============================================================================
// Dashboard
// ============================================================================

export async function getTicketsDashboard(
  params?: DashboardQueryParams
): Promise<TicketsDashboardResponse> {
  return api.get<TicketsDashboardResponse>("/api/v1/tickets/dashboard", {
    params: {
      period_months: params?.periodMonths,
    },
  });
}

// ============================================================================
// Ticket Types
// ============================================================================

export type TicketStatus = "open" | "in_progress" | "waiting" | "resolved" | "closed";
export type TicketPriority = "low" | "normal" | "high" | "urgent";
export type TicketCategory = "support" | "billing" | "technical" | "feature_request" | "bug" | "other";

export interface TicketMessage {
  id: string;
  ticketId: string;
  content: string;
  isInternal: boolean;
  author: {
    id: string;
    name: string;
    email: string;
    type: "customer" | "agent" | "system";
  };
  attachments?: Array<{
    id: string;
    name: string;
    url: string;
    size: number;
    mimeType: string;
  }>;
  createdAt: string;
}

export interface Ticket {
  id: string;
  number: string;
  subject: string;
  description: string;
  status: TicketStatus;
  priority: TicketPriority;
  category: TicketCategory;
  customer: {
    id: string;
    name: string;
    email: string;
  };
  assignee?: {
    id: string;
    name: string;
    email: string;
  };
  tags?: string[];
  sla?: {
    responseDeadline?: string;
    resolutionDeadline?: string;
    isBreached: boolean;
  };
  messageCount: number;
  lastMessageAt?: string;
  createdAt: string;
  updatedAt: string;
  resolvedAt?: string;
  closedAt?: string;
}

// ============================================================================
// Ticket CRUD
// ============================================================================

export interface GetTicketsParams {
  page?: number;
  pageSize?: number;
  status?: TicketStatus;
  priority?: TicketPriority;
  category?: TicketCategory;
  assigneeId?: string;
  customerId?: string;
  search?: string;
  tags?: string[];
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

export async function getTickets(params: GetTicketsParams = {}): Promise<{
  tickets: Ticket[];
  totalCount: number;
  pageCount: number;
}> {
  const {
    page = 1,
    pageSize = 20,
    status,
    priority,
    category,
    assigneeId,
    customerId,
    search,
    tags,
    sortBy,
    sortOrder,
  } = params;

  const response = await api.get<unknown>("/api/v1/tickets", {
    params: {
      page,
      page_size: pageSize,
      status,
      priority,
      category,
      assignee_id: assigneeId,
      customer_id: customerId,
      search,
      tags: tags?.join(","),
      sort_by: sortBy,
      sort_order: sortOrder,
    },
  });
  const normalized = normalizePaginatedResponse<Ticket>(response);

  return {
    tickets: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
  };
}

export async function getTicket(id: string): Promise<Ticket> {
  return api.get<Ticket>(`/api/v1/tickets/${id}`);
}

export interface CreateTicketData {
  subject: string;
  description: string;
  priority?: TicketPriority;
  category?: TicketCategory;
  customerId?: string;
  tags?: string[];
}

export async function createTicket(data: CreateTicketData): Promise<Ticket> {
  return api.post<Ticket>("/api/v1/tickets", {
    subject: data.subject,
    description: data.description,
    priority: data.priority,
    category: data.category,
    customer_id: data.customerId,
    tags: data.tags,
  });
}

export interface UpdateTicketData {
  subject?: string;
  description?: string;
  status?: TicketStatus;
  priority?: TicketPriority;
  category?: TicketCategory;
  assigneeId?: string;
  tags?: string[];
}

export async function updateTicket(id: string, data: UpdateTicketData): Promise<Ticket> {
  return api.patch<Ticket>(`/api/v1/tickets/${id}`, {
    subject: data.subject,
    description: data.description,
    status: data.status,
    priority: data.priority,
    category: data.category,
    assignee_id: data.assigneeId,
    tags: data.tags,
  });
}

export async function deleteTicket(id: string): Promise<void> {
  return api.delete(`/api/v1/tickets/${id}`);
}

export async function updateTicketStatus(
  id: string,
  status: string,
  resolution?: string
): Promise<Ticket> {
  void resolution;
  return updateTicket(id, { status: status as TicketStatus });
}

export async function addTicketTags(ticketId: string, tags: string[]): Promise<Ticket> {
  const ticket = await getTicket(ticketId);
  const combined = [...(ticket.tags ?? []), ...tags];
  const deduped: string[] = [];
  const seen = new Set<string>();

  for (const tag of combined) {
    if (!seen.has(tag)) {
      seen.add(tag);
      deduped.push(tag);
    }
  }

  return updateTicket(ticketId, { tags: deduped });
}

export async function removeTicketTag(ticketId: string, tag: string): Promise<Ticket> {
  const ticket = await getTicket(ticketId);
  const nextTags = (ticket.tags ?? []).filter((value) => value !== tag);
  return updateTicket(ticketId, { tags: nextTags });
}

export async function linkTickets(
  _ticketId: string,
  _linkedTicketId: string,
  _linkType: string
): Promise<void> {
  throw new ApiClientError("Linking tickets is not supported", 501, "NOT_IMPLEMENTED");
}

// ============================================================================
// Ticket Messages
// ============================================================================

export async function getTicketMessages(ticketId: string): Promise<TicketMessage[]> {
  return api.get<TicketMessage[]>(`/api/v1/tickets/${ticketId}/messages`);
}

export async function addTicketMessage(
  ticketId: string,
  data: {
    content: string;
    isInternal?: boolean;
    attachmentIds?: string[];
  }
): Promise<TicketMessage> {
  return api.post<TicketMessage>(`/api/v1/tickets/${ticketId}/messages`, {
    content: data.content,
    is_internal: data.isInternal,
    attachment_ids: data.attachmentIds,
  });
}

// ============================================================================
// Ticket Assignment
// ============================================================================

export async function assignTicket(ticketId: string, assigneeId: string): Promise<Ticket> {
  return api.patch<Ticket>(`/api/v1/tickets/${ticketId}`, {
    assignee_id: assigneeId,
  });
}

export async function autoAssignTicket(ticketId: string): Promise<Ticket> {
  return api.post<Ticket>(`/api/v1/tickets/${ticketId}/assign/auto`);
}

export async function unassignTicket(ticketId: string): Promise<Ticket> {
  return api.patch<Ticket>(`/api/v1/tickets/${ticketId}`, {
    assignee_id: null,
  });
}

// ============================================================================
// Ticket Statistics
// ============================================================================

export interface TicketStats {
  total: number;
  byStatus: Record<TicketStatus, number>;
  byPriority: Record<TicketPriority, number>;
  byCategory: Record<TicketCategory, number>;
  avgResponseTime: number;
  avgResolutionTime: number;
  slaBreachCount: number;
}

export async function getTicketStats(params?: {
  startDate?: string;
  endDate?: string;
}): Promise<TicketStats> {
  return api.get<TicketStats>("/api/v1/tickets/stats", {
    params: {
      start_date: params?.startDate,
      end_date: params?.endDate,
    },
  });
}

export interface TicketMetrics {
  openTickets: number;
  resolvedToday: number;
  avgFirstResponseTime: number;
  avgResolutionTime: number;
  customerSatisfaction: number;
  ticketsTrend: Array<{
    date: string;
    created: number;
    resolved: number;
  }>;
}

export async function getTicketMetrics(periodDays: number = 30): Promise<TicketMetrics> {
  return api.get<TicketMetrics>("/api/v1/tickets/metrics", {
    params: { period_days: periodDays },
  });
}

// ============================================================================
// Agent Performance
// ============================================================================

export interface AgentPerformance {
  userId: string;
  name: string;
  assignedCount: number;
  resolvedCount: number;
  avgResolutionTime: number;
  avgResponseTime: number;
  customerSatisfaction: number;
  activeTickets: number;
}

export async function getAgentPerformance(params?: {
  periodDays?: number;
}): Promise<AgentPerformance[]> {
  return api.get<AgentPerformance[]>("/api/v1/tickets/agents/performance", {
    params: { period_days: params?.periodDays },
  });
}

// ============================================================================
// Agent Availability
// ============================================================================

export interface AgentAvailability {
  userId: string;
  name: string;
  status: "available" | "busy" | "away" | "offline";
  activeTicketCount: number;
  maxTickets: number;
  lastActivityAt: string;
}

export async function getAgentAvailability(): Promise<AgentAvailability[]> {
  return api.get<AgentAvailability[]>("/api/v1/tickets/agents/availability");
}

export async function updateAgentAvailability(status: AgentAvailability["status"]): Promise<void> {
  return api.post("/api/v1/tickets/agents/availability", { status });
}
