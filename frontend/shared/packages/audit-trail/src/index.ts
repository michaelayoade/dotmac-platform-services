/**
 * @dotmac/audit-trail
 *
 * Audit trail and compliance monitoring for DotMac Framework
 * Provides React hooks and components for audit logging and compliance dashboards
 */

// Main hooks
export { useAuditTrail } from './hooks/useAuditTrail';
export { useAuditEvents } from './hooks/useAuditEvents';
export { useComplianceReport } from './hooks/useComplianceReport';
export { useAnomalyDetection } from './hooks/useAnomalyDetection';

// Components
export { AuditEventsList } from './components/AuditEventsList';
export { ComplianceDashboard } from './components/ComplianceDashboard';
export { AuditChart } from './components/AuditChart';
export { AnomalyAlert } from './components/AnomalyAlert';
export { EventTimeline } from './components/EventTimeline';

// Context and providers
export { AuditTrailProvider, useAuditTrailContext } from './providers/AuditTrailProvider';

// Types
export type {
  AuditEvent,
  AuditCategory,
  AuditLevel,
  AuditEventFilter,
  ComplianceReport,
  AnomalyAlert as AnomalyAlertType,
  AuditMetrics,
  ExportFormat,
  AuditTrailConfig,
} from './types';

// Utilities
export { auditLogger } from './utils/auditLogger';
export { formatAuditEvent, formatComplianceData } from './utils/formatters';
export { exportAuditData } from './utils/export';