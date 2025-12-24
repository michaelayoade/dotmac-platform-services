"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getJobs,
  getJob,
  createJob,
  cancelJob,
  retryJob,
  getJobProgress,
  getJobLogs,
  getScheduledJobs,
  getScheduledJob,
  createScheduledJob,
  updateScheduledJob,
  deleteScheduledJob,
  pauseScheduledJob,
  resumeScheduledJob,
  triggerScheduledJob,
  getJobStats,
  getJobQueues,
  purgeQueue,
  type GetJobsParams,
  type Job,
  type JobProgress,
  type JobLog,
  type ScheduledJob,
  type CreateJobData,
  type CreateScheduledJobData,
  type JobStats,
  type JobQueue,
} from "@/lib/api/jobs";
import { queryKeys } from "@/lib/api/query-keys";

type JobStatsParams = Parameters<typeof getJobStats> extends [infer P] ? P : undefined;
type JobStatsArgs = Parameters<typeof getJobStats>;

// ============================================================================
// Jobs Hooks
// ============================================================================

export function useJobs(params?: GetJobsParams) {
  return useQuery({
    queryKey: queryKeys.jobs.list(params),
    queryFn: () => getJobs(params),
    placeholderData: (previousData) => previousData,
  });
}

export function useJob(id: string) {
  return useQuery({
    queryKey: queryKeys.jobs.detail(id),
    queryFn: () => getJob(id),
    enabled: !!id,
    refetchInterval: (query) => {
      // Poll while job is running
      const data = query.state.data as Job | undefined;
      if (data?.status === "running" || data?.status === "pending") {
        return 2000;
      }
      return false;
    },
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createJob,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.jobs.all,
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.jobs.stats(),
      });
    },
  });
}

export function useCancelJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: cancelJob,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.jobs.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.jobs.all,
      });
    },
  });
}

export function useRetryJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: retryJob,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.jobs.all,
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.jobs.stats(),
      });
    },
  });
}

export function useJobProgress(id: string) {
  return useQuery({
    queryKey: queryKeys.jobs.progress(id),
    queryFn: () => getJobProgress(id),
    enabled: !!id,
    refetchInterval: 1000, // Poll every second for progress
  });
}

export function useJobLogs(id: string) {
  return useQuery({
    queryKey: queryKeys.jobs.logs(id),
    queryFn: () => getJobLogs(id),
    enabled: !!id,
  });
}

// ============================================================================
// Scheduled Jobs Hooks
// ============================================================================

export function useScheduledJobs() {
  return useQuery({
    queryKey: queryKeys.jobs.scheduled.all(),
    queryFn: () => getScheduledJobs(),
  });
}

export function useScheduledJob(id: string) {
  return useQuery({
    queryKey: queryKeys.jobs.scheduled.detail(id),
    queryFn: () => getScheduledJob(id),
    enabled: !!id,
  });
}

export function useCreateScheduledJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createScheduledJob,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.jobs.scheduled.all(),
      });
    },
  });
}

export function useUpdateScheduledJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateScheduledJobData> }) =>
      updateScheduledJob(id, data),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.jobs.scheduled.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.jobs.scheduled.all(),
      });
    },
  });
}

export function useDeleteScheduledJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteScheduledJob,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.jobs.scheduled.all(),
      });
    },
  });
}

export function usePauseScheduledJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: pauseScheduledJob,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.jobs.scheduled.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.jobs.scheduled.all(),
      });
    },
  });
}

export function useResumeScheduledJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: resumeScheduledJob,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.jobs.scheduled.detail(data.id), data);
      queryClient.invalidateQueries({
        queryKey: queryKeys.jobs.scheduled.all(),
      });
    },
  });
}

export function useTriggerScheduledJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: triggerScheduledJob,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.jobs.all,
      });
    },
  });
}

// ============================================================================
// Job Stats & Queues Hooks
// ============================================================================

export function useJobStats(params?: JobStatsParams) {
  const args = (params === undefined ? [] : [params]) as JobStatsArgs;

  return useQuery({
    queryKey: queryKeys.jobs.stats(params),
    queryFn: () => getJobStats(...args),
    staleTime: 30 * 1000,
  });
}

export function useJobQueues() {
  return useQuery({
    queryKey: queryKeys.jobs.queues(),
    queryFn: getJobQueues,
    refetchInterval: 10 * 1000, // Poll every 10 seconds
  });
}

export function usePurgeQueue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: purgeQueue,
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.jobs.queues(),
      });
      queryClient.invalidateQueries({
        queryKey: queryKeys.jobs.stats(),
      });
    },
  });
}

// ============================================================================
// Re-export types
// ============================================================================

export type {
  GetJobsParams,
  Job,
  JobProgress,
  JobLog,
  ScheduledJob,
  CreateJobData,
  CreateScheduledJobData,
  JobStats,
  JobQueue,
};
