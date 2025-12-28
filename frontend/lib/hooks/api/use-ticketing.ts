"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getTickets,
  getTicket,
  createTicket,
  updateTicket,
  deleteTicket,
  getTicketMessages,
  addTicketMessage,
  assignTicket,
  autoAssignTicket,
  updateTicketStatus,
  addTicketTags,
  removeTicketTag,
  linkTickets,
  getTicketStats,
  getAgentPerformance,
  getTicketsDashboard,
  type GetTicketsParams,
  type Ticket,
  type TicketMessage,
  type TicketStatus,
  type CreateTicketData,
  type UpdateTicketData,
  type TicketStats,
  type AgentPerformance,
} from "@/lib/api/ticketing";
import { queryKeys } from "@/lib/api/query-keys";
import type { DashboardQueryParams } from "@/lib/api/types/dashboard";

type TicketStatsParams = Parameters<typeof getTicketStats> extends [infer P] ? P : undefined;

// ============================================================================
// Ticketing Dashboard Hook
// ============================================================================

export function useTicketsDashboard(params?: DashboardQueryParams) {
  return useQuery({
    queryKey: queryKeys.ticketing.dashboard(params),
    queryFn: () => getTicketsDashboard(params),
    staleTime: 60 * 1000, // 1 minute
  });
}

// ============================================================================
// Tickets Hooks
// ============================================================================

export function useTickets(params?: GetTicketsParams) {
  return useQuery({
    queryKey: queryKeys.ticketing.tickets.list(params),
    queryFn: () => getTickets(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useTicket(id: string) {
  return useQuery({
    queryKey: queryKeys.ticketing.tickets.detail(id),
    queryFn: () => getTicket(id),
    enabled: !!id,
  });
}

export function useCreateTicket() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createTicket,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.ticketing.tickets.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.ticketing.stats(),
      });
    },
  });
}

export function useUpdateTicket() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateTicketData }) =>
      updateTicket(id, data),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.ticketing.tickets.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.ticketing.tickets.all(),
      });
    },
  });
}

export function useDeleteTicket() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: deleteTicket,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.ticketing.tickets.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.ticketing.stats(),
      });
    },
  });
}

// ============================================================================
// Ticket Messages Hooks
// ============================================================================

export function useTicketMessages(ticketId: string) {
  return useQuery({
    queryKey: queryKeys.ticketing.tickets.messages(ticketId),
    queryFn: () => getTicketMessages(ticketId),
    enabled: !!ticketId,
    refetchInterval: 30 * 1000, // Poll for new messages
  });
}

export function useAddTicketMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      ticketId,
      message,
      isInternal,
      attachments,
    }: {
      ticketId: string;
      message: string;
      isInternal?: boolean;
      attachments?: string[];
    }) =>
      addTicketMessage(ticketId, {
        content: message,
        isInternal,
        attachmentIds: attachments,
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.ticketing.tickets.messages(variables.ticketId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.ticketing.tickets.detail(variables.ticketId),
      });
    },
  });
}

// ============================================================================
// Ticket Assignment Hooks
// ============================================================================

export function useAssignTicket() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ ticketId, agentId }: { ticketId: string; agentId: string }) =>
      assignTicket(ticketId, agentId),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.ticketing.tickets.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.ticketing.tickets.all(),
      });
    },
  });
}

export function useAutoAssignTicket() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: autoAssignTicket,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.ticketing.tickets.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.ticketing.tickets.all(),
      });
    },
  });
}

// ============================================================================
// Ticket Status Hooks
// ============================================================================

export function useUpdateTicketStatus() {
  const queryClient = useQueryClient();

  return useMutation<
    Ticket,
    Error,
    { ticketId: string; status: TicketStatus; resolution?: string }
  >({
    mutationFn: ({
      ticketId,
      status,
      resolution,
    }: {
      ticketId: string;
      status: TicketStatus;
      resolution?: string;
    }) => updateTicketStatus(ticketId, status, resolution),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.ticketing.tickets.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.ticketing.tickets.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.ticketing.stats(),
      });
    },
  });
}

// ============================================================================
// Ticket Tags Hooks
// ============================================================================

export function useAddTicketTags() {
  const queryClient = useQueryClient();

  return useMutation<Ticket, Error, { ticketId: string; tags: string[] }>({
    mutationFn: ({ ticketId, tags }: { ticketId: string; tags: string[] }) =>
      addTicketTags(ticketId, tags),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.ticketing.tickets.detail(data.id), data);
    },
  });
}

export function useRemoveTicketTag() {
  const queryClient = useQueryClient();

  return useMutation<Ticket, Error, { ticketId: string; tag: string }>({
    mutationFn: ({ ticketId, tag }: { ticketId: string; tag: string }) =>
      removeTicketTag(ticketId, tag),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.ticketing.tickets.detail(data.id), data);
    },
  });
}

// ============================================================================
// Ticket Linking Hook
// ============================================================================

export function useLinkTickets() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      ticketId,
      linkedTicketId,
      linkType,
    }: {
      ticketId: string;
      linkedTicketId: string;
      linkType: string;
    }) => linkTickets(ticketId, linkedTicketId, linkType),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.ticketing.tickets.detail(variables.ticketId),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.ticketing.tickets.detail(variables.linkedTicketId),
      });
    },
  });
}

// ============================================================================
// Ticket Stats Hooks
// ============================================================================

export function useTicketStats(params?: TicketStatsParams) {
  return useQuery({
    queryKey: queryKeys.ticketing.stats(params),
    queryFn: () => getTicketStats(params),
    staleTime: 2 * 60 * 1000,
  });
}

export function useAgentPerformance(params?: { periodDays?: number; agentId?: string }) {
  return useQuery({
    queryKey: queryKeys.ticketing.agentPerformance(params),
    queryFn: () => getAgentPerformance(params),
    staleTime: 5 * 60 * 1000,
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  GetTicketsParams,
  Ticket,
  TicketMessage,
  CreateTicketData,
  TicketStats,
  AgentPerformance,
};
