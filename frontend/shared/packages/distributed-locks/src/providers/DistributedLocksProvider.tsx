import React, { createContext, useContext, ReactNode } from 'react';
import type { DistributedLocksConfig } from '../types';

interface DistributedLocksContextValue extends DistributedLocksConfig {
  // Additional context methods can be added here
}

const DistributedLocksContext = createContext<DistributedLocksContextValue | null>(null);

interface DistributedLocksProviderProps {
  children: ReactNode;
  config: DistributedLocksConfig;
}

export function DistributedLocksProvider({ children, config }: DistributedLocksProviderProps) {
  const contextValue: DistributedLocksContextValue = {
    ...config,
  };

  return (
    <DistributedLocksContext.Provider value={contextValue}>
      {children}
    </DistributedLocksContext.Provider>
  );
}

export function useDistributedLocksContext(): DistributedLocksContextValue {
  const context = useContext(DistributedLocksContext);
  if (!context) {
    throw new Error('useDistributedLocksContext must be used within a DistributedLocksProvider');
  }
  return context;
}