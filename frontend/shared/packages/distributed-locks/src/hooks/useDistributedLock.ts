import { useState, useEffect, useCallback, useRef } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { LockInfo, LockStatus } from '../types';
import { useDistributedLocksContext } from '../providers/DistributedLocksProvider';
import { createLockKey, isLockExpired } from '../utils/lockUtils';

export interface UseDistributedLockOptions {
  resource: string;
  userId?: string;
  ttl?: number; // Time to live in seconds
  autoRenew?: boolean;
  renewInterval?: number; // Seconds
  onLockAcquired?: (lock: LockInfo) => void;
  onLockLost?: (lock: LockInfo) => void;
  onLockExpired?: (lock: LockInfo) => void;
}

export function useDistributedLock({
  resource,
  userId,
  ttl = 300, // 5 minutes default
  autoRenew = true,
  renewInterval = 60, // 1 minute default
  onLockAcquired,
  onLockLost,
  onLockExpired,
}: UseDistributedLockOptions) {
  const { apiClient, config } = useDistributedLocksContext();
  const queryClient = useQueryClient();
  const [lockStatus, setLockStatus] = useState<LockStatus>('idle');
  const [currentLock, setCurrentLock] = useState<LockInfo | null>(null);
  const renewalTimerRef = useRef<NodeJS.Timeout | null>(null);

  const lockKey = createLockKey(resource, userId);

  // Query to check lock status
  const {
    data: lockInfo,
    isLoading: isChecking,
    error: checkError,
  } = useQuery({
    queryKey: ['lock', lockKey],
    queryFn: async (): Promise<LockInfo | null> => {
      try {
        const response = await apiClient.get(`/api/locks/${lockKey}`);
        return response.data;
      } catch (error: any) {
        if (error.response?.status === 404) {
          return null; // Lock doesn't exist
        }
        throw error;
      }
    },
    refetchInterval: config.pollingInterval || 5000,
    enabled: lockStatus !== 'idle',
  });

  // Mutation to acquire lock
  const acquireLock = useMutation({
    mutationFn: async (): Promise<LockInfo> => {
      const response = await apiClient.post(`/api/locks/${lockKey}`, {
        ttl,
        metadata: {
          resource,
          userId,
          timestamp: new Date().toISOString(),
        },
      });
      return response.data;
    },
    onSuccess: (lock) => {
      setLockStatus('acquired');
      setCurrentLock(lock);
      onLockAcquired?.(lock);

      // Start auto-renewal if enabled
      if (autoRenew) {
        startRenewal(lock);
      }

      queryClient.invalidateQueries({ queryKey: ['lock', lockKey] });
    },
    onError: (error: any) => {
      if (error.response?.status === 409) {
        setLockStatus('conflict');
      } else {
        setLockStatus('error');
      }
    },
  });

  // Mutation to release lock
  const releaseLock = useMutation({
    mutationFn: async (lockId: string) => {
      await apiClient.delete(`/api/locks/${lockKey}/${lockId}`);
    },
    onSuccess: () => {
      setLockStatus('released');
      setCurrentLock(null);
      stopRenewal();
      queryClient.invalidateQueries({ queryKey: ['lock', lockKey] });
    },
  });

  // Mutation to renew lock
  const renewLock = useMutation({
    mutationFn: async (lockId: string): Promise<LockInfo> => {
      const response = await apiClient.patch(`/api/locks/${lockKey}/${lockId}/renew`, {
        ttl,
      });
      return response.data;
    },
    onSuccess: (lock) => {
      setCurrentLock(lock);
    },
    onError: (error: any) => {
      if (error.response?.status === 404 || error.response?.status === 410) {
        // Lock expired or lost
        setLockStatus('expired');
        setCurrentLock(null);
        stopRenewal();
        onLockExpired?.(currentLock!);
      }
    },
  });

  // Start auto-renewal timer
  const startRenewal = useCallback((lock: LockInfo) => {
    if (renewalTimerRef.current) {
      clearInterval(renewalTimerRef.current);
    }

    renewalTimerRef.current = setInterval(() => {
      if (currentLock && !isLockExpired(currentLock)) {
        renewLock.mutate(currentLock.id);
      } else {
        stopRenewal();
        setLockStatus('expired');
        onLockExpired?.(currentLock!);
      }
    }, renewInterval * 1000);
  }, [renewLock, renewInterval, currentLock, onLockExpired]);

  // Stop auto-renewal timer
  const stopRenewal = useCallback(() => {
    if (renewalTimerRef.current) {
      clearInterval(renewalTimerRef.current);
      renewalTimerRef.current = null;
    }
  }, []);

  // Check for lock conflicts
  useEffect(() => {
    if (lockInfo && currentLock && lockInfo.id !== currentLock.id) {
      // Someone else acquired the lock
      setLockStatus('conflict');
      setCurrentLock(null);
      stopRenewal();
      onLockLost?.(currentLock);
    } else if (lockInfo && !currentLock && lockStatus === 'waiting') {
      // Lock became available
      setLockStatus('available');
    }
  }, [lockInfo, currentLock, lockStatus, onLockLost]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopRenewal();
      if (currentLock && config.autoRelease) {
        releaseLock.mutate(currentLock.id);
      }
    };
  }, [currentLock, config.autoRelease, releaseLock, stopRenewal]);

  // Public API
  const tryAcquire = useCallback(() => {
    if (lockStatus === 'idle' || lockStatus === 'available') {
      setLockStatus('acquiring');
      acquireLock.mutate();
    }
  }, [lockStatus, acquireLock]);

  const release = useCallback(() => {
    if (currentLock) {
      releaseLock.mutate(currentLock.id);
    }
  }, [currentLock, releaseLock]);

  const forceRelease = useCallback(async () => {
    if (lockInfo) {
      await apiClient.delete(`/api/locks/${lockKey}/${lockInfo.id}?force=true`);
      queryClient.invalidateQueries({ queryKey: ['lock', lockKey] });
    }
  }, [lockInfo, apiClient, lockKey, queryClient]);

  const waitForLock = useCallback(() => {
    setLockStatus('waiting');
  }, []);

  return {
    // State
    lockStatus,
    currentLock,
    conflictingLock: lockInfo && lockInfo.id !== currentLock?.id ? lockInfo : null,

    // Computed state
    isOwner: currentLock?.owner === (userId || config.defaultUserId),
    isLocked: !!lockInfo,
    isAvailable: !lockInfo,
    timeRemaining: currentLock ?
      Math.max(0, new Date(currentLock.expiresAt).getTime() - Date.now()) / 1000 : 0,

    // Loading states
    isAcquiring: acquireLock.isPending,
    isReleasing: releaseLock.isPending,
    isRenewing: renewLock.isPending,
    isChecking,

    // Error states
    error: acquireLock.error || releaseLock.error || renewLock.error || checkError,

    // Actions
    tryAcquire,
    release,
    forceRelease,
    waitForLock,
    renew: () => currentLock && renewLock.mutate(currentLock.id),

    // Manual control
    startRenewal: () => currentLock && startRenewal(currentLock),
    stopRenewal,
  };
}