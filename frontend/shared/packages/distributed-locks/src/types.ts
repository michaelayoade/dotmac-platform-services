/**
 * Type definitions for distributed locks
 */

export interface LockInfo {
  id: string;
  resource: string;
  owner: string;
  acquiredAt: string;
  expiresAt: string;
  ttl: number;
  metadata?: Record<string, any>;
  renewCount?: number;
}

export type LockStatus =
  | 'idle'         // Initial state, no lock operation attempted
  | 'acquiring'    // Currently trying to acquire lock
  | 'acquired'     // Successfully acquired lock
  | 'waiting'      // Waiting for lock to become available
  | 'available'    // Lock is available to acquire
  | 'conflict'     // Lock conflict detected
  | 'expired'      // Lock has expired
  | 'released'     // Lock was released
  | 'error';       // Error occurred

export interface OptimisticUpdateConfig<T = any> {
  resource: string;
  optimisticUpdate: (current: T, update: Partial<T>) => T;
  rollback: (original: T, failed: T) => T;
  conflictResolver?: ConflictResolutionStrategy<T>;
  retryAttempts?: number;
  retryDelay?: number;
}

export type ConflictResolutionStrategy<T = any> =
  | 'latest-wins'
  | 'merge'
  | 'manual'
  | ((local: T, remote: T, original: T) => T | Promise<T>);

export interface LockConflict<T = any> {
  id: string;
  resource: string;
  localVersion: T;
  remoteVersion: T;
  originalVersion: T;
  conflictingFields: string[];
  timestamp: string;
  status: 'pending' | 'resolved' | 'rejected';
}

export interface DistributedLocksConfig {
  apiClient: any; // HTTP client instance
  defaultUserId?: string;
  pollingInterval?: number; // milliseconds
  autoRelease?: boolean;
  defaultTtl?: number; // seconds
  maxRetries?: number;
  retryDelay?: number; // milliseconds
}

export interface OptimisticUpdateResult<T = any> {
  data: T;
  isOptimistic: boolean;
  isPending: boolean;
  error: Error | null;
  conflicts: LockConflict<T>[];
}

export interface LockManagerState {
  locks: Record<string, LockInfo>;
  conflicts: LockConflict[];
  pendingOperations: string[];
}