/**
 * React Query hooks for admin settings management
 *
 * Connects to backend admin settings API:
 * - GET /api/v1/admin/settings/categories - List all categories
 * - GET /api/v1/admin/settings/category/{category} - Get category settings
 * - PUT /api/v1/admin/settings/category/{category} - Update category settings
 * - POST /api/v1/admin/settings/validate - Validate settings
 * - GET /api/v1/admin/settings/audit-logs - Get audit logs
 */

import { useQuery, useMutation, useQueryClient, type UseQueryOptions } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';
import { useToast } from '@/hooks/use-toast';

// ============================================
// Types matching backend admin/settings models
// ============================================

export type SettingsCategory =
  | 'database'
  | 'jwt'
  | 'redis'
  | 'vault'
  | 'storage'
  | 'email'
  | 'tenant'
  | 'cors'
  | 'rate_limit'
  | 'observability'
  | 'celery'
  | 'features'
  | 'billing';

export interface SettingField {
  name: string;
  value: any;
  type: string;
  description?: string | null;
  default?: any;
  required: boolean;
  sensitive: boolean;
  validation_rules?: Record<string, any> | null;
}

export interface SettingsResponse {
  category: SettingsCategory;
  display_name: string;
  fields: SettingField[];
  last_updated?: string | null;
  updated_by?: string | null;
}

export interface SettingsCategoryInfo {
  category: SettingsCategory;
  display_name: string;
  description: string;
  fields_count: number;
  has_sensitive_fields: boolean;
  restart_required: boolean;
  last_updated?: string | null;
}

export interface SettingsUpdateRequest {
  updates: Record<string, any>;
  validate_only?: boolean;
  restart_required?: boolean;
  reason?: string | null;
}

export interface SettingsValidationResult {
  valid: boolean;
  errors: Record<string, string>;
  warnings: Record<string, string>;
  restart_required: boolean;
}

export interface AuditLog {
  id: string;
  timestamp: string;
  user_id: string;
  user_email: string;
  category: SettingsCategory;
  action: string;
  changes: Record<string, { old: any; new: any }>;
  reason?: string | null;
  ip_address?: string | null;
  user_agent?: string | null;
}

// ============================================
// Query Hooks
// ============================================

/**
 * Fetch all settings categories
 */
export function useSettingsCategories(options?: UseQueryOptions<SettingsCategoryInfo[], Error>) {
  return useQuery<SettingsCategoryInfo[], Error>({
    queryKey: ['settings', 'categories'],
    queryFn: async () => {
      const response = await apiClient.get<SettingsCategoryInfo[]>('/admin/settings/categories');
      return response.data;
    },
    ...options,
  });
}

/**
 * Fetch settings for a specific category
 */
export function useCategorySettings(
  category: SettingsCategory,
  includeSensitive: boolean = false,
  options?: UseQueryOptions<SettingsResponse, Error>
) {
  return useQuery<SettingsResponse, Error>({
    queryKey: ['settings', 'category', category, includeSensitive],
    queryFn: async () => {
      const response = await apiClient.get<SettingsResponse>(
        `/admin/settings/category/${category}`,
        {
          params: { include_sensitive: includeSensitive },
        }
      );
      return response.data;
    },
    enabled: !!category,
    ...options,
  });
}

/**
 * Fetch audit logs for settings changes
 */
export function useAuditLogs(
  category?: SettingsCategory | null,
  userId?: string | null,
  limit: number = 100,
  options?: UseQueryOptions<AuditLog[], Error>
) {
  return useQuery<AuditLog[], Error>({
    queryKey: ['settings', 'audit-logs', category, userId, limit],
    queryFn: async () => {
      const response = await apiClient.get<AuditLog[]>('/admin/settings/audit-logs', {
        params: {
          category: category || undefined,
          user_id: userId || undefined,
          limit,
        },
      });
      return response.data;
    },
    ...options,
  });
}

// ============================================
// Mutation Hooks
// ============================================

/**
 * Update category settings
 */
export function useUpdateCategorySettings() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: async ({
      category,
      data,
    }: {
      category: SettingsCategory;
      data: SettingsUpdateRequest;
    }) => {
      const response = await apiClient.put<SettingsResponse>(
        `/admin/settings/category/${category}`,
        data
      );
      return response.data;
    },
    onSuccess: (data, variables) => {
      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ['settings', 'categories'] });
      queryClient.invalidateQueries({ queryKey: ['settings', 'category', variables.category] });
      queryClient.invalidateQueries({ queryKey: ['settings', 'audit-logs'] });

      toast({
        title: 'Settings updated',
        description: `${data.display_name} settings were updated successfully.`,
      });
    },
    onError: (error: any) => {
      toast({
        title: 'Update failed',
        description: error.response?.data?.detail || 'Failed to update settings',
        variant: 'destructive',
      });
    },
  });
}

/**
 * Validate settings before applying
 */
export function useValidateSettings() {
  return useMutation({
    mutationFn: async ({
      category,
      updates,
    }: {
      category: SettingsCategory;
      updates: Record<string, any>;
    }) => {
      const response = await apiClient.post<SettingsValidationResult>(
        '/admin/settings/validate',
        updates,
        {
          params: { category },
        }
      );
      return response.data;
    },
  });
}

// ============================================
// Utility Functions
// ============================================

/**
 * Get category display name
 */
export function getCategoryDisplayName(category: SettingsCategory): string {
  const displayNames: Record<SettingsCategory, string> = {
    database: 'Database Configuration',
    jwt: 'JWT & Authentication',
    redis: 'Redis Cache',
    vault: 'Vault/Secrets Management',
    storage: 'Object Storage (MinIO/S3)',
    email: 'Email & SMTP',
    tenant: 'Multi-tenancy',
    cors: 'CORS Configuration',
    rate_limit: 'Rate Limiting',
    observability: 'Logging & Monitoring',
    celery: 'Background Tasks',
    features: 'Feature Flags',
    billing: 'Billing & Subscriptions',
  };
  return displayNames[category] || category;
}

/**
 * Format last updated timestamp
 */
export function formatLastUpdated(timestamp: string | null | undefined): string {
  if (!timestamp) return 'Never';

  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 30) return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;

  return date.toLocaleDateString();
}

/**
 * Mask sensitive field value
 */
export function maskSensitiveValue(value: any, sensitive: boolean): string {
  if (!sensitive) return String(value);
  if (!value) return '';

  const str = String(value);
  if (str.length <= 4) return '***';
  return str.substring(0, 4) + '***';
}
