/**
 * @dotmac/distributed-locks
 *
 * Distributed locking and optimistic updates for DotMac Framework
 * Provides React hooks for managing distributed locks and handling conflicts
 */

// Main hooks
export { useDistributedLock } from './hooks/useDistributedLock';
export { useOptimisticUpdate } from './hooks/useOptimisticUpdate';
export { useLockManager } from './hooks/useLockManager';
export { useConflictResolution } from './hooks/useConflictResolution';

// Components
export { LockIndicator } from './components/LockIndicator';
export { ConflictDialog } from './components/ConflictDialog';
export { OptimisticEditForm } from './components/OptimisticEditForm';

// Context and providers
export { DistributedLocksProvider, useDistributedLocksContext } from './providers/DistributedLocksProvider';

// HOCs and decorators
export { withOptimisticUpdate } from './hoc/withOptimisticUpdate';
export { withLockProtection } from './hoc/withLockProtection';

// Types
export type {
  LockInfo,
  LockStatus,
  OptimisticUpdateConfig,
  ConflictResolutionStrategy,
  LockConflict,
  DistributedLocksConfig,
} from './types';

// Utilities
export { createLockKey, isLockExpired } from './utils/lockUtils';
export { resolveConflict } from './utils/conflictResolver';