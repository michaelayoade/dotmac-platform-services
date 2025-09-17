// Main entry point for @dotmac/analytics package
export * from './types';
export * from './components';
export * from './hooks';
export * from './services';
export * from './utils';

// Context
export { AnalyticsProvider, AnalyticsContext } from './context/AnalyticsContext';

// Main service
export { AnalyticsService } from './services/AnalyticsService';

// Package info
export const version = '1.0.0';
export const name = '@dotmac/analytics';
