import { useContext } from 'react';
import { AnalyticsContext } from '../context/AnalyticsContext';
import type { AnalyticsContextValue } from '../types';

export const useAnalytics = (): AnalyticsContextValue => {
  const context = useContext(AnalyticsContext);

  if (!context) {
    throw new Error('useAnalytics must be used within an AnalyticsProvider');
  }

  return context;
};
