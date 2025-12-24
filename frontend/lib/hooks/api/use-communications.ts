"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  sendEmail,
  sendBulkEmails,
  getEmailTemplates,
  getEmailTemplate,
  createEmailTemplate,
  updateEmailTemplate,
  deleteEmailTemplate,
  previewEmailTemplate,
  testEmailTemplate,
  queueBulkEmail,
  getBulkEmailJob,
  cancelBulkEmailJob,
  getEmailLogs,
  getEmailLog,
  resendEmail,
  getCommunicationStats,
  type EmailRequest,
  type EmailResponse,
  type GetTemplatesParams,
  type EmailTemplate,
  type CreateEmailTemplateData,
  type BulkEmailJob,
  type GetEmailLogsParams,
  type EmailLog,
  type CommunicationStats,
} from "@/lib/api/communications";
import { queryKeys } from "@/lib/api/query-keys";

// ============================================================================
// Email Sending Hooks
// ============================================================================

export function useSendEmail() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: sendEmail,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.communications.logs.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.communications.stats(),
      });
    },
  });
}

export function useSendBulkEmails() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: sendBulkEmails,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.communications.logs.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.communications.stats(),
      });
    },
  });
}

// ============================================================================
// Email Templates Hooks
// ============================================================================

export function useEmailTemplates(params?: GetTemplatesParams) {
  return useQuery({
    queryKey: queryKeys.communications.templates.list(params),
    queryFn: () => getEmailTemplates(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useEmailTemplate(id: string) {
  return useQuery({
    queryKey: queryKeys.communications.templates.detail(id),
    queryFn: () => getEmailTemplate(id),
    enabled: !!id,
  });
}

export function useCreateEmailTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createEmailTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.communications.templates.all(),
      });
    },
  });
}

export function useUpdateEmailTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateEmailTemplateData> }) =>
      updateEmailTemplate(id, data),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.communications.templates.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.communications.templates.all(),
      });
    },
  });
}

export function useDeleteEmailTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteEmailTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.communications.templates.all(),
      });
    },
  });
}

export function usePreviewEmailTemplate() {
  return useMutation({
    mutationFn: ({
      templateId,
      variables,
    }: {
      templateId: string;
      variables?: Record<string, unknown>;
    }) => previewEmailTemplate(templateId, variables),
  });
}

export function useTestEmailTemplate() {
  return useMutation({
    mutationFn: ({
      templateId,
      testEmail,
      variables,
    }: {
      templateId: string;
      testEmail: string;
      variables?: Record<string, unknown>;
    }) => testEmailTemplate(templateId, testEmail, variables),
  });
}

// ============================================================================
// Bulk Email Hooks
// ============================================================================

export function useQueueBulkEmail() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: queueBulkEmail,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.communications.bulkJobs.all(),
      });
    },
  });
}

export function useBulkEmailJob(jobId: string) {
  return useQuery({
    queryKey: queryKeys.communications.bulkJobs.detail(jobId),
    queryFn: () => getBulkEmailJob(jobId),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const data = query.state.data as BulkEmailJob | undefined;
      if (data?.status === "processing" || data?.status === "queued") {
        return 3000; // Poll every 3 seconds
      }
      return false;
    },
  });
}

export function useCancelBulkEmailJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: cancelBulkEmailJob,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.communications.bulkJobs.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.communications.bulkJobs.all(),
      });
    },
  });
}

// ============================================================================
// Email Logs Hooks
// ============================================================================

export function useEmailLogs(params?: GetEmailLogsParams) {
  return useQuery({
    queryKey: queryKeys.communications.logs.list(params),
    queryFn: () => getEmailLogs(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useEmailLog(id: string) {
  return useQuery({
    queryKey: queryKeys.communications.logs.detail(id),
    queryFn: () => getEmailLog(id),
    enabled: !!id,
  });
}

export function useResendEmail() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: resendEmail,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.communications.logs.all(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.communications.stats(),
      });
    },
  });
}

// ============================================================================
// Communication Stats Hook
// ============================================================================

export function useCommunicationStats(params?: { periodDays?: number }) {
  return useQuery({
    queryKey: queryKeys.communications.stats(params),
    queryFn: () => getCommunicationStats(params),
    staleTime: 5 * 60 * 1000,
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  EmailRequest,
  EmailResponse,
  GetTemplatesParams,
  EmailTemplate,
  CreateEmailTemplateData,
  BulkEmailJob,
  GetEmailLogsParams,
  EmailLog,
  CommunicationStats,
};
