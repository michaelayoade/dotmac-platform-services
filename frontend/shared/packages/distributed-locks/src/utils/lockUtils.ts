import type { LockInfo } from '../types';

/**
 * Create a standardized lock key from resource and optional user ID
 */
export function createLockKey(resource: string, userId?: string): string {
  const sanitizedResource = resource.replace(/[^a-zA-Z0-9_-]/g, '_');
  if (userId) {
    const sanitizedUserId = userId.replace(/[^a-zA-Z0-9_-]/g, '_');
    return `${sanitizedResource}:${sanitizedUserId}`;
  }
  return sanitizedResource;
}

/**
 * Check if a lock has expired
 */
export function isLockExpired(lock: LockInfo): boolean {
  return new Date(lock.expiresAt).getTime() <= Date.now();
}

/**
 * Calculate time remaining for a lock in seconds
 */
export function getLockTimeRemaining(lock: LockInfo): number {
  const remaining = new Date(lock.expiresAt).getTime() - Date.now();
  return Math.max(0, Math.floor(remaining / 1000));
}

/**
 * Format lock duration for display
 */
export function formatLockDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`;
  } else if (seconds < 3600) {
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
}

/**
 * Generate a unique lock ID
 */
export function generateLockId(): string {
  return `lock_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * Validate lock resource name
 */
export function validateResourceName(resource: string): boolean {
  // Allow alphanumeric characters, hyphens, underscores, and forward slashes
  return /^[a-zA-Z0-9_/-]+$/.test(resource);
}

/**
 * Calculate optimal TTL based on operation type
 */
export function calculateOptimalTTL(operationType: 'read' | 'write' | 'critical'): number {
  switch (operationType) {
    case 'read':
      return 60; // 1 minute for read operations
    case 'write':
      return 300; // 5 minutes for write operations
    case 'critical':
      return 900; // 15 minutes for critical operations
    default:
      return 300;
  }
}