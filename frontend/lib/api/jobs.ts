/**
 * Jobs API
 *
 * Async job management, progress tracking, and scheduling
 */

import { api, ApiClientError, normalizePaginatedResponse } from "./client";
import type { JobsDashboardResponse, DashboardQueryParams } from "./types/dashboard";

// ============================================================================
// Dashboard
// ============================================================================

export async function getJobsDashboard(
  params?: DashboardQueryParams
): Promise<JobsDashboardResponse> {
  return api.get<JobsDashboardResponse>("/api/v1/jobs/dashboard", {
    params: {
      period_days: params?.periodDays,
    },
  });
}

// ============================================================================
// Job Types
// ============================================================================

export type JobStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed"
  | "cancelled"
  | "assigned"
  | string;
export type JobType = string;

export interface JobSummary {
  id: string;
  jobType: JobType;
  status: JobStatus;
  title: string;
  progressPercent: number;
  itemsTotal?: number | null;
  itemsProcessed: number;
  itemsSucceeded: number;
  itemsFailed: number;
  createdBy: string;
  createdAt: string;
  startedAt?: string | null;
  completedAt?: string | null;
  durationSeconds?: number | null;
}

export interface Job {
  id: string;
  tenantId: string;
  jobType: JobType;
  status: JobStatus;
  title: string;
  description?: string | null;
  progressPercent: number;
  itemsTotal?: number | null;
  itemsProcessed: number;
  itemsSucceeded: number;
  itemsFailed: number;
  currentItem?: string | null;
  errorMessage?: string | null;
  errorDetails?: Record<string, unknown> | null;
  errorTraceback?: string | null;
  failedItems?: unknown[] | null;
  parameters?: Record<string, unknown> | null;
  result?: Record<string, unknown> | null;
  createdBy: string;
  cancelledBy?: string | null;
  createdAt: string;
  startedAt?: string | null;
  completedAt?: string | null;
  cancelledAt?: string | null;
  isTerminal: boolean;
  isActive: boolean;
  successRate: number;
  failureRate: number;
  durationSeconds?: number | null;
}

// ============================================================================
// Job CRUD
// ============================================================================

export interface GetJobsParams {
  page?: number;
  pageSize?: number;
  jobType?: JobType;
  jobStatus?: JobStatus;
}

export async function getJobs(params: GetJobsParams = {}): Promise<{
  jobs: JobSummary[];
  totalCount: number;
  pageCount: number;
  hasMore?: boolean;
}> {
  const { page = 1, pageSize = 50, jobType, jobStatus } = params;

  const response = await api.get<unknown>("/api/v1/jobs", {
    params: {
      page,
      pageSize,
      jobType,
      jobStatus,
    },
  });

  const normalized = normalizePaginatedResponse<JobSummary>(response);

  return {
    jobs: normalized.items,
    totalCount: normalized.total,
    pageCount: normalized.totalPages,
    hasMore: normalized.hasNext,
  };
}

export async function getJob(id: string): Promise<Job> {
  return api.get<Job>(`/api/v1/jobs/${id}`);
}

export interface CreateJobData {
  jobType: JobType;
  title: string;
  description?: string;
  itemsTotal?: number;
  parameters?: Record<string, unknown>;
}

export async function createJob(data: CreateJobData): Promise<Job> {
  return api.post<Job>("/api/v1/jobs", data);
}

export interface JobCancelResponse {
  id: string;
  status: JobStatus;
  cancelledAt: string;
  cancelledBy: string;
  message: string;
}

export async function cancelJob(id: string): Promise<JobCancelResponse> {
  return api.post<JobCancelResponse>(`/api/v1/jobs/${id}/cancel`);
}

export interface JobRetryResponse {
  originalJobId: string;
  newJobId: string;
  failedItemsCount: number;
  message: string;
}

export async function retryJob(id: string): Promise<JobRetryResponse> {
  return api.post<JobRetryResponse>(`/api/v1/jobs/${id}/retry`);
}

export async function updateJobProgress(
  id: string,
  progress: {
    progressPercent?: number;
    itemsProcessed?: number;
    itemsSucceeded?: number;
    itemsFailed?: number;
    status?: JobStatus;
    errorMessage?: string;
    errorDetails?: Record<string, unknown>;
    errorTraceback?: string;
    result?: Record<string, unknown>;
  }
): Promise<Job> {
  return api.patch<Job>(`/api/v1/jobs/${id}`, progress);
}

// ============================================================================
// Job Progress & Logs
// ============================================================================

export interface JobProgress {
  jobId: string;
  status: JobStatus;
  progressPercent: number;
  itemsProcessed: number;
  itemsSucceeded: number;
  itemsFailed: number;
  currentItem?: string | null;
}

export async function getJobProgress(id: string): Promise<JobProgress> {
  const job = await getJob(id);
  return {
    jobId: job.id,
    status: job.status,
    progressPercent: job.progressPercent,
    itemsProcessed: job.itemsProcessed,
    itemsSucceeded: job.itemsSucceeded,
    itemsFailed: job.itemsFailed,
    currentItem: job.currentItem,
  };
}

export interface JobLog {
  id: string;
  level: string;
  message: string;
  timestamp: string;
}

export async function getJobLogs(_id: string): Promise<JobLog[]> {
  return [];
}

// ============================================================================
// Job Statistics
// ============================================================================

export interface JobStats {
  totalJobs: number;
  pendingJobs: number;
  runningJobs: number;
  completedJobs: number;
  failedJobs: number;
  cancelledJobs: number;
  avgDurationSeconds?: number | null;
  totalItemsProcessed: number;
  totalItemsSucceeded: number;
  totalItemsFailed: number;
  overallSuccessRate: number;
}

export async function getJobStats(params?: { periodDays?: number }): Promise<JobStats> {
  return api.get<JobStats>("/api/v1/jobs/statistics", {
    params: {
      periodDays: params?.periodDays,
    },
  });
}

// ============================================================================
// Scheduled Jobs
// ============================================================================

export interface ScheduledJob {
  id: string;
  tenantId: string;
  name: string;
  description?: string | null;
  jobType: JobType;
  cronExpression?: string | null;
  intervalSeconds?: number | null;
  isActive: boolean;
  maxConcurrentRuns: number;
  timeoutSeconds?: number | null;
  priority: string;
  maxRetries: number;
  retryDelaySeconds: number;
  lastRunAt?: string | null;
  nextRunAt?: string | null;
  totalRuns: number;
  successfulRuns: number;
  failedRuns: number;
  createdBy: string;
  createdAt: string;
}

export interface CreateScheduledJobData {
  name: string;
  jobType: JobType;
  cronExpression?: string;
  intervalSeconds?: number;
  description?: string;
  parameters?: Record<string, unknown>;
  priority?: string;
  maxRetries?: number;
  retryDelaySeconds?: number;
  maxConcurrentRuns?: number;
  timeoutSeconds?: number;
}

export async function getScheduledJobs(params?: {
  isActive?: boolean;
  page?: number;
  pageSize?: number;
}): Promise<ScheduledJob[]> {
  return api.get<ScheduledJob[]>("/api/v1/jobs/scheduler/scheduled-jobs", {
    params,
  });
}

export async function getScheduledJob(id: string): Promise<ScheduledJob> {
  return api.get<ScheduledJob>(`/api/v1/jobs/scheduler/scheduled-jobs/${id}`);
}

export async function createScheduledJob(data: CreateScheduledJobData): Promise<ScheduledJob> {
  return api.post<ScheduledJob>("/api/v1/jobs/scheduler/scheduled-jobs", data);
}

export async function updateScheduledJob(
  id: string,
  data: Partial<CreateScheduledJobData> & { isActive?: boolean }
): Promise<ScheduledJob> {
  return api.patch<ScheduledJob>(`/api/v1/jobs/scheduler/scheduled-jobs/${id}`, data);
}

export async function deleteScheduledJob(id: string): Promise<void> {
  return api.delete(`/api/v1/jobs/scheduler/scheduled-jobs/${id}`);
}

export async function pauseScheduledJob(id: string): Promise<ScheduledJob> {
  return api.post<ScheduledJob>(`/api/v1/jobs/scheduler/scheduled-jobs/${id}/toggle`, undefined, {
    params: { isActive: false },
  });
}

export async function resumeScheduledJob(id: string): Promise<ScheduledJob> {
  return api.post<ScheduledJob>(`/api/v1/jobs/scheduler/scheduled-jobs/${id}/toggle`, undefined, {
    params: { isActive: true },
  });
}

export async function triggerScheduledJob(_id: string): Promise<void> {
  throw new ApiClientError("Triggering scheduled jobs is not supported", 501, "NOT_IMPLEMENTED");
}

// ============================================================================
// Job Queues
// ============================================================================

export interface JobQueue {
  name: string;
  size: number;
  active: number;
  delayed: number;
  failed: number;
}

export async function getJobQueues(): Promise<JobQueue[]> {
  throw new ApiClientError("Job queues are not available via the API", 501, "NOT_IMPLEMENTED");
}

export async function purgeQueue(_queueName: string): Promise<{ purged: boolean }> {
  throw new ApiClientError("Queue purge is not supported", 501, "NOT_IMPLEMENTED");
}

// ============================================================================
// Job Chains
// ============================================================================

export interface JobChain {
  id: string;
  name: string;
  chainDefinition: Array<{ jobType: JobType; parameters?: Record<string, unknown> }>;
  executionMode: "sequential" | "parallel";
  description?: string;
  stopOnFailure?: boolean;
  timeoutSeconds?: number;
}

export async function getJobChains(): Promise<JobChain[]> {
  return api.get<JobChain[]>("/api/v1/jobs/scheduler/chains");
}

export async function createJobChain(data: {
  name: string;
  chainDefinition: JobChain["chainDefinition"];
  executionMode?: JobChain["executionMode"];
  description?: string;
  stopOnFailure?: boolean;
  timeoutSeconds?: number;
}): Promise<JobChain> {
  return api.post<JobChain>("/api/v1/jobs/scheduler/chains", data);
}
