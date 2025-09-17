import React, { createContext, useContext, ReactNode } from 'react';
import type { AuditTrailConfig } from '../types';

interface AuditTrailContextValue extends AuditTrailConfig {
  // Additional context methods can be added here
}

const AuditTrailContext = createContext<AuditTrailContextValue | null>(null);

interface AuditTrailProviderProps {
  children: ReactNode;
  config: AuditTrailConfig;
}

export function AuditTrailProvider({ children, config }: AuditTrailProviderProps) {
  const contextValue: AuditTrailContextValue = {
    ...config,
  };

  return (
    <AuditTrailContext.Provider value={contextValue}>
      {children}
    </AuditTrailContext.Provider>
  );
}

export function useAuditTrailContext(): AuditTrailContextValue {
  const context = useContext(AuditTrailContext);
  if (!context) {
    throw new Error('useAuditTrailContext must be used within an AuditTrailProvider');
  }
  return context;
}