/**
 * Browser storage utilities with type safety and error handling
 * Consolidated from headless and primitives packages
 */

import { useEffect, useState, useCallback } from 'react';

// Storage interface for dependency injection and testing
export interface StorageInterface {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
  clear(): void;
}

// Safe storage wrapper that handles errors
class SafeStorage implements StorageInterface {
  constructor(private storage: Storage) {}

  getItem(key: string): string | null {
    try {
      return this.storage.getItem(key);
    } catch (error) {
      console.warn(`Storage getItem failed for key "${key}":`, error);
      return null;
    }
  }

  setItem(key: string, value: string): void {
    try {
      this.storage.setItem(key, value);
    } catch (error) {
      console.warn(`Storage setItem failed for key "${key}":`, error);
    }
  }

  removeItem(key: string): void {
    try {
      this.storage.removeItem(key);
    } catch (error) {
      console.warn(`Storage removeItem failed for key "${key}":`, error);
    }
  }

  clear(): void {
    try {
      this.storage.clear();
    } catch (error) {
      console.warn('Storage clear failed:', error);
    }
  }
}

// Create safe storage instances
export const safeLocalStorage =
  typeof window !== 'undefined' ? new SafeStorage(window.localStorage) : null;
export const safeSessionStorage =
  typeof window !== 'undefined' ? new SafeStorage(window.sessionStorage) : null;

// Generic storage utility functions
export function getStorageItem<T>(
  storage: StorageInterface | null,
  key: string,
  defaultValue: T
): T {
  if (!storage) return defaultValue;

  try {
    const item = storage.getItem(key);
    if (item === null) return defaultValue;
    return JSON.parse(item);
  } catch (error) {
    console.warn(`Failed to parse storage item "${key}":`, error);
    return defaultValue;
  }
}

export function setStorageItem<T>(storage: StorageInterface | null, key: string, value: T): void {
  if (!storage) return;

  try {
    storage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.warn(`Failed to set storage item "${key}":`, error);
  }
}

export function removeStorageItem(storage: StorageInterface | null, key: string): void {
  if (!storage) return;
  storage.removeItem(key);
}

// React hooks for storage
export function useLocalStorage<T>(key: string, defaultValue: T): [T, (value: T) => void] {
  const [storedValue, setStoredValue] = useState<T>(() =>
    getStorageItem(safeLocalStorage, key, defaultValue)
  );

  const setValue = useCallback(
    (value: T) => {
      setStoredValue(value);
      setStorageItem(safeLocalStorage, key, value);
    },
    [key]
  );

  // Listen for storage changes from other tabs
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === key && e.newValue !== null) {
        try {
          setStoredValue(JSON.parse(e.newValue));
        } catch (error) {
          console.warn(`Failed to parse storage change for "${key}":`, error);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [key]);

  return [storedValue, setValue];
}

export function useSessionStorage<T>(key: string, defaultValue: T): [T, (value: T) => void] {
  const [storedValue, setStoredValue] = useState<T>(() =>
    getStorageItem(safeSessionStorage, key, defaultValue)
  );

  const setValue = useCallback(
    (value: T) => {
      setStoredValue(value);
      setStorageItem(safeSessionStorage, key, value);
    },
    [key]
  );

  return [storedValue, setValue];
}

// Utility functions for common storage patterns
export function usePersistedState<T>(
  key: string,
  defaultValue: T,
  useSession = false
): [T, (value: T) => void] {
  return useSession ? useSessionStorage(key, defaultValue) : useLocalStorage(key, defaultValue);
}

// Storage management utilities
export function clearAllStorage(): void {
  safeLocalStorage?.clear();
  safeSessionStorage?.clear();
}

export function getStorageKeys(storage: StorageInterface | null): string[] {
  if (!storage || typeof window === 'undefined') return [];

  try {
    // Access the actual storage object to get keys
    const actualStorage =
      storage === safeLocalStorage ? window.localStorage : window.sessionStorage;
    return Object.keys(actualStorage);
  } catch (error) {
    console.warn('Failed to get storage keys:', error);
    return [];
  }
}

export function getStorageSize(storage: StorageInterface | null): number {
  if (!storage) return 0;

  try {
    const keys = getStorageKeys(storage);
    return keys.reduce((total, key) => {
      const item = storage.getItem(key);
      return total + (item?.length || 0);
    }, 0);
  } catch (error) {
    console.warn('Failed to calculate storage size:', error);
    return 0;
  }
}

// Expiring storage utilities
interface ExpiringStorageItem<T> {
  value: T;
  expiry: number;
}

export function setExpiringStorageItem<T>(
  storage: StorageInterface | null,
  key: string,
  value: T,
  ttlMs: number
): void {
  const expiry = Date.now() + ttlMs;
  const item: ExpiringStorageItem<T> = { value, expiry };
  setStorageItem(storage, key, item);
}

export function getExpiringStorageItem<T>(
  storage: StorageInterface | null,
  key: string,
  defaultValue: T
): T {
  if (!storage) return defaultValue;

  try {
    const item = storage.getItem(key);
    if (!item) return defaultValue;

    const parsed: ExpiringStorageItem<T> = JSON.parse(item);

    if (Date.now() > parsed.expiry) {
      storage.removeItem(key);
      return defaultValue;
    }

    return parsed.value;
  } catch (error) {
    console.warn(`Failed to get expiring storage item "${key}":`, error);
    return defaultValue;
  }
}

// Cache utilities
export function createStorageCache<T>(
  storage: StorageInterface | null,
  prefix: string,
  defaultTtl: number = 5 * 60 * 1000 // 5 minutes
) {
  return {
    get(key: string, defaultValue: T): T {
      return getExpiringStorageItem(storage, `${prefix}_${key}`, defaultValue);
    },

    set(key: string, value: T, ttl: number = defaultTtl): void {
      setExpiringStorageItem(storage, `${prefix}_${key}`, value, ttl);
    },

    remove(key: string): void {
      removeStorageItem(storage, `${prefix}_${key}`);
    },

    clear(): void {
      const keys = getStorageKeys(storage);
      keys
        .filter((key) => key.startsWith(`${prefix}_`))
        .forEach((key) => removeStorageItem(storage, key));
    },
  };
}
