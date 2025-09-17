# @dotmac/audit-trail

Comprehensive audit trail and compliance monitoring for DotMac Framework applications.

## Features

- **Audit Logging**: Track all user actions and system events
- **Compliance Reporting**: Generate compliance reports for various frameworks
- **Anomaly Detection**: Identify unusual patterns and security threats
- **Real-time Monitoring**: Live audit event streaming and alerts
- **Export Capabilities**: Export audit data in multiple formats

## Installation

```bash
pnpm install @dotmac/audit-trail
```

## Quick Start

### Provider Setup

```tsx
import { AuditTrailProvider } from '@dotmac/audit-trail';
import { httpClient } from '@dotmac/http-client';

function App() {
  return (
    <AuditTrailProvider
      config={{
        apiClient: httpClient,
        currentUserId: 'current-user-id',
        refreshInterval: 30000,
        enableRealTimeAlerts: true,
        anomalyDetection: {
          enabled: true,
          threshold: 0.8,
          checkInterval: 60000,
        },
      }}
    >
      <YourApp />
    </AuditTrailProvider>
  );
}
```

### Audit Logging

```tsx
import { useAuditTrail } from '@dotmac/audit-trail';

function UserActions() {
  const { logUserAction, logSecurityEvent } = useAuditTrail();

  const handleFileDownload = (fileId: string) => {
    // Log the user action
    logUserAction('file_download', `file:${fileId}`, {
      fileName: 'document.pdf',
      fileSize: 1024000,
      downloadMethod: 'direct',
    });

    // Perform the actual download
    downloadFile(fileId);
  };

  const handleSuspiciousActivity = () => {
    // Log security event
    logSecurityEvent('suspicious_login_pattern', 'high', {
      attempts: 5,
      timeWindow: '5m',
      ipAddress: '192.168.1.100',
      userAgent: 'Mozilla/5.0...',
    });
  };

  return (
    <div>
      <button onClick={() => handleFileDownload('file-123')}>
        Download File
      </button>
    </div>
  );
}
```

### Viewing Audit Events

```tsx
import { useAuditTrail } from '@dotmac/audit-trail';
import { AuditEventsList, AuditTimeline } from '@dotmac/audit-trail';

function AuditDashboard() {
  const {
    events,
    isLoading,
    searchEvents,
    recentEvents,
    criticalEvents,
    securityEvents,
  } = useAuditTrail();

  const handleSearch = async () => {
    const results = await searchEvents({
      categories: ['AUTHENTICATION', 'SECURITY_EVENT'],
      start_time: '2024-01-01T00:00:00Z',
      end_time: '2024-01-31T23:59:59Z',
      limit: 100,
    });
    console.log('Search results:', results);
  };

  if (isLoading) {
    return <div>Loading audit events...</div>;
  }

  return (
    <div>
      <h2>Audit Dashboard</h2>

      {/* Recent critical events */}
      <div>
        <h3>Critical Events ({criticalEvents.length})</h3>
        <AuditEventsList
          events={criticalEvents}
          maxItems={10}
          showDetails={true}
        />
      </div>

      {/* Security events timeline */}
      <div>
        <h3>Security Events Timeline</h3>
        <AuditTimeline
          events={securityEvents}
          groupBy="day"
          showFilters={true}
        />
      </div>

      {/* All events */}
      <div>
        <h3>All Events ({events.length})</h3>
        <AuditEventsList
          events={events}
          pagination={true}
          itemsPerPage={25}
          sortable={true}
        />
      </div>

      <button onClick={handleSearch}>
        Search Events
      </button>
    </div>
  );
}
```

### Compliance Reporting

```tsx
import { useComplianceReports } from '@dotmac/audit-trail';
import { ComplianceReport } from '@dotmac/audit-trail';

function ComplianceDashboard() {
  const {
    currentReport,
    generateReport,
    exportReport,
    isGenerating,
    complianceScore,
    complianceIssues,
  } = useComplianceReports();

  const handleGenerateReport = async () => {
    await generateReport({
      framework: 'SOX',
      startDate: '2024-01-01',
      endDate: '2024-12-31',
      includeRecommendations: true,
    });
  };

  const handleExportReport = async () => {
    await exportReport('pdf');
  };

  return (
    <div>
      <h2>Compliance Dashboard</h2>

      <div>
        <h3>Compliance Score: {complianceScore}%</h3>
        <p>Issues: {complianceIssues.length}</p>
      </div>

      {currentReport && (
        <ComplianceReport
          report={currentReport}
          showMetrics={true}
          showRecommendations={true}
          onExport={handleExportReport}
        />
      )}

      <button onClick={handleGenerateReport} disabled={isGenerating}>
        {isGenerating ? 'Generating...' : 'Generate Report'}
      </button>
    </div>
  );
}
```

### Anomaly Detection

```tsx
import { useAnomalyDetection } from '@dotmac/audit-trail';
import { AnomalyAlert } from '@dotmac/audit-trail';

function SecurityMonitoring() {
  const {
    anomalies,
    activeAlerts,
    resolveAnomaly,
    markFalsePositive,
  } = useAnomalyDetection();

  const handleResolveAnomaly = async (anomalyId: string) => {
    await resolveAnomaly(anomalyId, {
      resolution: 'Investigated and confirmed as normal behavior',
      investigatedBy: 'security-team',
    });
  };

  return (
    <div>
      <h2>Anomaly Detection</h2>

      <div>
        <h3>Active Alerts ({activeAlerts.length})</h3>
        {activeAlerts.map(anomaly => (
          <AnomalyAlert
            key={anomaly.id}
            anomaly={anomaly}
            onResolve={() => handleResolveAnomaly(anomaly.id)}
            onMarkFalsePositive={() => markFalsePositive(anomaly.id)}
            showInvestigation={true}
          />
        ))}
      </div>

      <div>
        <h3>All Anomalies ({anomalies.length})</h3>
        {anomalies.map(anomaly => (
          <div key={anomaly.id}>
            <strong>{anomaly.title}</strong> - {anomaly.severity}
            <p>{anomaly.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

## API Reference

### Hooks

#### `useAuditTrail(options?)`

Main hook for audit trail operations.

**Options:**
- `autoRefresh`: Enable auto-refresh (default: true)
- `refreshInterval`: Refresh interval in ms (default: 30000)
- `pageSize`: Number of events per page (default: 50)

**Returns:**
- `events`: Array of audit events
- `searchEvents()`: Search function
- `logUserAction()`: Log user action
- `logSecurityEvent()`: Log security event
- `exportAuditData()`: Export data function
- `complianceScore`: Current compliance score
- `anomalies`: Detected anomalies

#### `useAuditEvents(filter?)`

Hook for filtered audit events.

**Parameters:**
- `filter`: AuditEventFilter object

**Returns:**
- `events`: Filtered events
- `totalCount`: Total number of events
- `isLoading`: Loading state
- `refetch()`: Refresh events

#### `useComplianceReports()`

Hook for compliance reporting.

**Returns:**
- `currentReport`: Current compliance report
- `generateReport()`: Generate new report
- `exportReport()`: Export report function
- `complianceScore`: Overall compliance score
- `complianceIssues`: Current issues

### Components

#### `<AuditEventsList />`

**Props:**
- `events`: Array of audit events
- `maxItems`: Maximum items to display
- `showDetails`: Show event details
- `pagination`: Enable pagination
- `sortable`: Enable sorting
- `onEventClick`: Event click handler

#### `<AuditTimeline />`

**Props:**
- `events`: Array of audit events
- `groupBy`: 'hour' | 'day' | 'week' | 'month'
- `showFilters`: Show filter controls
- `interactive`: Enable timeline interaction

#### `<ComplianceReport />`

**Props:**
- `report`: Compliance report data
- `showMetrics`: Display metrics section
- `showRecommendations`: Display recommendations
- `onExport`: Export handler

#### `<AnomalyAlert />`

**Props:**
- `anomaly`: Anomaly data
- `onResolve`: Resolve handler
- `onMarkFalsePositive`: False positive handler
- `showInvestigation`: Show investigation details

### Types

```typescript
interface AuditEvent {
  id: string;
  timestamp: string;
  category: AuditCategory;
  level: AuditLevel;
  action: string;
  resource: string;
  actor: string;
  details: Record<string, any>;
  outcome: 'success' | 'failure' | 'denied';
}

type AuditCategory =
  | 'AUTHENTICATION'
  | 'AUTHORIZATION'
  | 'DATA_ACCESS'
  | 'SECURITY_EVENT'
  | 'USER_MANAGEMENT'
  | 'SYSTEM_CHANGE';

type AuditLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';

interface ComplianceReport {
  id: string;
  framework: string;
  score: number;
  issues: ComplianceIssue[];
  recommendations: string[];
  generatedAt: string;
}
```

## Compliance Frameworks

Supported compliance frameworks:
- **SOX**: Sarbanes-Oxley Act compliance
- **GDPR**: General Data Protection Regulation
- **HIPAA**: Health Insurance Portability and Accountability Act
- **PCI DSS**: Payment Card Industry Data Security Standard
- **ISO 27001**: Information Security Management

## Export Formats

- **JSON**: Machine-readable format
- **CSV**: Spreadsheet-compatible format
- **PDF**: Human-readable reports
- **Excel**: Advanced spreadsheet format

## Best Practices

1. **Log Important Actions**: Log all user actions that modify data
2. **Security Events**: Always log authentication and authorization events
3. **Data Access**: Track access to sensitive data
4. **System Changes**: Log configuration and system changes
5. **Regular Reviews**: Review audit logs regularly for anomalies