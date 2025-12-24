// API Response Types
// Standardized API response shapes for the platform

/**
 * Standard paginated response wrapper
 */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNext?: boolean;
  hasPrev?: boolean;
}

/**
 * Standard API error response
 */
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, string[]>;
  requestId?: string;
  timestamp: string;
}

/**
 * Standard success response wrapper
 */
export interface ApiResponse<T> {
  data: T;
  message?: string;
  requestId?: string;
}

/**
 * Bulk operation result
 */
export interface BulkOperationResult {
  total: number;
  succeeded: number;
  failed: number;
  errors?: Array<{
    id: string;
    error: string;
  }>;
}

/**
 * Sort configuration
 */
export interface SortConfig {
  field: string;
  direction: "asc" | "desc";
}

/**
 * Filter configuration
 */
export interface FilterConfig {
  field: string;
  operator: "eq" | "neq" | "gt" | "gte" | "lt" | "lte" | "contains" | "startsWith" | "endsWith" | "in";
  value: string | number | boolean | string[] | number[];
}

/**
 * Query parameters for list endpoints
 */
export interface ListQueryParams {
  page?: number;
  pageSize?: number;
  sort?: SortConfig[];
  filters?: FilterConfig[];
  search?: string;
}

/**
 * Date range filter
 */
export interface DateRange {
  start: string; // ISO date string
  end: string; // ISO date string
}

/**
 * Webhook event payload
 */
export interface WebhookEvent<T = unknown> {
  id: string;
  type: string;
  timestamp: string;
  tenantId: string;
  data: T;
  signature: string;
}
