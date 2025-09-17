export interface AuditEvent {
  id: string;
  category: AuditCategory;
  action: string;
  level: AuditLevel;
  user_id?: string;
  tenant_id?: string;
  resource_type?: string;
  resource_id?: string;
  ip_address?: string;
  user_agent?: string;
  metadata: Record<string, any>;
  outcome: 'success' | 'failure' | 'denied';
  timestamp: string;
  correlation_id?: string;
}

export type AuditCategory =
  | 'AUTHENTICATION'
  | 'AUTHORIZATION'
  | 'DATA_ACCESS'
  | 'DATA_CHANGE'
  | 'SYSTEM_CHANGE'
  | 'SECURITY_EVENT'
  | 'COMPLIANCE'
  | 'CONFIGURATION'
  | 'USER_MANAGEMENT'
  | 'SYSTEM_TASK';

export type AuditLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';

export interface AuditEventFilter {
  start_time?: string;
  end_time?: string;
  categories?: AuditCategory[];
  levels?: AuditLevel[];
  user_id?: string;
  tenant_id?: string;
  outcome?: ('success' | 'failure' | 'denied')[];
  search_term?: string;
  limit?: number;
  offset?: number;
}

export interface ComplianceReport {
  id: string;
  report_type: string;
  start_date: string;
  end_date: string;
  generated_at: string;
  summary: {
    total_events: number;
    security_events: number;
    failed_logins: number;
    data_access_events: number;
    privileged_actions: number;
  };
  compliance_score: number;
  recommendations: string[];
  violations: ComplianceViolation[];
  export_url?: string;
}

export interface ComplianceViolation {
  id: string;
  rule: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  event_ids: string[];
  detected_at: string;
  resolved_at?: string;
}

export interface AnomalyAlert {
  id: string;
  type: 'unusual_activity' | 'security_threat' | 'performance_issue';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  affected_services?: string[];
  event_count: number;
  time_window: string;
  detected_at: string;
  resolved_at?: string;
  recommendations: string[];
  related_events: string[];
}

export interface AuditMetrics {
  period: string;
  total_events: number;
  events_by_category: Record<AuditCategory, number>;
  events_by_level: Record<AuditLevel, number>;
  events_by_outcome: Record<'success' | 'failure' | 'denied', number>;
  top_users: Array<{ user_id: string; event_count: number }>;
  top_actions: Array<{ action: string; event_count: number }>;
  hourly_distribution: Array<{ hour: number; count: number }>;
}

export type ExportFormat = 'json' | 'csv' | 'pdf' | 'xlsx';

export interface AuditTrailConfig {
  apiBaseUrl: string;
  enableRealTimeAlerts: boolean;
  refreshInterval: number;
  pageSize: number;
  exportFormats: ExportFormat[];
  anomalyDetection: {
    enabled: boolean;
    threshold: number;
    checkInterval: number;
  };
}

export interface EventTimeline {
  date: string;
  events: AuditEvent[];
}

export interface AuditSearchResult {
  events: AuditEvent[];
  total: number;
  page: number;
  pageSize: number;
  aggregations: {
    categories: Record<AuditCategory, number>;
    levels: Record<AuditLevel, number>;
    outcomes: Record<string, number>;
  };
}