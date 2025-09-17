import React, { createContext, useContext, ReactNode } from 'react';
import type { ServiceRegistryConfig } from '../types';

interface ServiceRegistryContextValue extends ServiceRegistryConfig {
  // Additional context methods can be added here
}

const ServiceRegistryContext = createContext<ServiceRegistryContextValue | null>(null);

interface ServiceRegistryProviderProps {
  children: ReactNode;
  config: ServiceRegistryConfig;
}

export function ServiceRegistryProvider({ children, config }: ServiceRegistryProviderProps) {
  const contextValue: ServiceRegistryContextValue = {
    ...config,
  };

  return (
    <ServiceRegistryContext.Provider value={contextValue}>
      {children}
    </ServiceRegistryContext.Provider>
  );
}

export function useServiceRegistryContext(): ServiceRegistryContextValue {
  const context = useContext(ServiceRegistryContext);
  if (!context) {
    throw new Error('useServiceRegistryContext must be used within a ServiceRegistryProvider');
  }
  return context;
}