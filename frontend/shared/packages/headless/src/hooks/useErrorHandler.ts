/**
 * Standard Error Handler Hook - NO BACKWARD COMPATIBILITY
 * Use only useStandardErrorHandler for all error handling
 */

// NO LEGACY COMPATIBILITY - Import useStandardErrorHandler directly
export { useStandardErrorHandler as useErrorHandler } from './useStandardErrorHandler';

// Breaking change: Legacy useErrorHandler interfaces removed
// Migration: Replace with useStandardErrorHandler
