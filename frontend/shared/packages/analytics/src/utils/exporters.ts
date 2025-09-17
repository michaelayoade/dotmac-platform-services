import type { AnalyticsDashboard, TimeSeries, KPIMetric, QueryResult } from '../types';

// CSV Export
export const exportToCsv = (data: any[], filename: string = 'export.csv'): void => {
  if (data.length === 0) {
    throw new Error('No data to export');
  }

  // Get headers from first object
  const headers = Object.keys(data[0]);
  const csvContent = [
    headers.join(','),
    ...data.map((row) =>
      headers
        .map((header) => {
          const value = row[header];
          // Handle values that might contain commas or quotes
          if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
            return `"${value.replace(/"/g, '""')}"`;
          }
          return value;
        })
        .join(',')
    ),
  ].join('\n');

  downloadFile(csvContent, filename, 'text/csv');
};

// Excel Export (simple CSV format - for full Excel support, would need additional library)
export const exportToExcel = (
  data: any[] | Record<string, any[]>,
  filename: string = 'export.xlsx'
): void => {
  if (Array.isArray(data)) {
    // Single sheet
    exportToCsv(data, filename.replace('.xlsx', '.csv'));
  } else {
    // Multiple sheets - create a zip file with multiple CSV files
    const sheets: Array<{ name: string; data: string }> = [];

    for (const [sheetName, sheetData] of Object.entries(data)) {
      if (sheetData.length === 0) continue;

      const headers = Object.keys(sheetData[0]);
      const csvContent = [
        headers.join(','),
        ...sheetData.map((row) =>
          headers
            .map((header) => {
              const value = row[header];
              if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                return `"${value.replace(/"/g, '""')}"`;
              }
              return value;
            })
            .join(',')
        ),
      ].join('\n');

      sheets.push({ name: sheetName, data: csvContent });
    }

    // For now, just export the first sheet
    if (sheets.length > 0) {
      downloadFile(sheets[0].data, filename.replace('.xlsx', '.csv'), 'text/csv');
    }
  }
};

// PDF Export (simplified - would need PDF library for full support)
export const exportToPdf = (
  content: string | AnalyticsDashboard,
  filename: string = 'export.pdf'
): void => {
  let htmlContent: string;

  if (typeof content === 'string') {
    htmlContent = content;
  } else {
    // Convert dashboard to HTML
    htmlContent = dashboardToHtml(content);
  }

  // Create a new window and print (browser will show print dialog with PDF option)
  const printWindow = window.open('', '_blank');
  if (printWindow) {
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>${filename}</title>
        <style>
          body { font-family: Arial, sans-serif; margin: 20px; }
          table { border-collapse: collapse; width: 100%; margin: 20px 0; }
          th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          th { background-color: #f2f2f2; }
          .metric-card { border: 1px solid #ddd; padding: 15px; margin: 10px; display: inline-block; min-width: 200px; }
          .metric-value { font-size: 24px; font-weight: bold; color: #333; }
          .metric-name { font-size: 14px; color: #666; margin-bottom: 5px; }
          @media print {
            body { margin: 0; }
            .no-print { display: none; }
          }
        </style>
      </head>
      <body>
        ${htmlContent}
      </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.focus();

    // Trigger print dialog
    setTimeout(() => {
      printWindow.print();
      printWindow.close();
    }, 250);
  } else {
    throw new Error('Unable to open print window');
  }
};

// Time Series Export
export const exportTimeSeriesData = (
  timeSeries: TimeSeries[],
  format: 'csv' | 'json',
  filename?: string
): void => {
  if (format === 'json') {
    const jsonData = JSON.stringify(timeSeries, null, 2);
    downloadFile(jsonData, filename || 'timeseries.json', 'application/json');
    return;
  }

  // CSV format
  const csvData: any[] = [];

  timeSeries.forEach((series) => {
    series.data.forEach((point) => {
      csvData.push({
        metricId: series.metricId,
        timestamp: point.timestamp.toISOString(),
        value: point.value,
        ...point.metadata,
        ...point.tags,
      });
    });
  });

  exportToCsv(csvData, filename || 'timeseries.csv');
};

// KPI Metrics Export
export const exportKPIMetrics = (
  metrics: KPIMetric[],
  format: 'csv' | 'json',
  filename?: string
): void => {
  if (format === 'json') {
    const jsonData = JSON.stringify(metrics, null, 2);
    downloadFile(jsonData, filename || 'kpi-metrics.json', 'application/json');
    return;
  }

  // CSV format
  const csvData = metrics.map((metric) => ({
    id: metric.id,
    name: metric.name,
    value: metric.value,
    previousValue: metric.previousValue,
    target: metric.target,
    unit: metric.unit,
    trend: metric.trend,
    trendPercentage: metric.trendPercentage,
    status: metric.status,
    category: metric.category,
    updatedAt: metric.updatedAt.toISOString(),
    description: metric.description,
    formula: metric.formula,
  }));

  exportToCsv(csvData, filename || 'kpi-metrics.csv');
};

// Query Results Export
export const exportQueryResults = (
  queryResult: QueryResult,
  format: 'csv' | 'json',
  filename?: string
): void => {
  if (format === 'json') {
    const jsonData = JSON.stringify(queryResult, null, 2);
    downloadFile(jsonData, filename || 'query-results.json', 'application/json');
    return;
  }

  // CSV format
  const headers = queryResult.columns.map((col) => col.name);
  const csvData = queryResult.rows.map((row) => {
    const rowObj: any = {};
    headers.forEach((header, index) => {
      rowObj[header] = row[index];
    });
    return rowObj;
  });

  exportToCsv(csvData, filename || 'query-results.csv');
};

// Helper function to download file
const downloadFile = (content: string, filename: string, mimeType: string): void => {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.display = 'none';

  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  // Clean up the URL object
  setTimeout(() => URL.revokeObjectURL(url), 100);
};

// Helper function to convert dashboard to HTML
const dashboardToHtml = (dashboard: AnalyticsDashboard): string => {
  const widgetHtml = dashboard.widgets
    .map((widget) => {
      switch (widget.type) {
        case 'metric':
        case 'kpi':
          return `
          <div class="metric-card">
            <div class="metric-name">${widget.title}</div>
            <div class="metric-value">-</div>
            <div class="metric-description">${widget.description || ''}</div>
          </div>
        `;

        case 'chart':
          return `
          <div class="chart-container">
            <h3>${widget.title}</h3>
            <p>Chart visualization would appear here</p>
            ${widget.description ? `<p><small>${widget.description}</small></p>` : ''}
          </div>
        `;

        case 'table':
          return `
          <div class="table-container">
            <h3>${widget.title}</h3>
            <table>
              <thead>
                <tr>
                  <th>Column 1</th>
                  <th>Column 2</th>
                  <th>Column 3</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td colspan="3">Table data would appear here</td>
                </tr>
              </tbody>
            </table>
            ${widget.description ? `<p><small>${widget.description}</small></p>` : ''}
          </div>
        `;

        default:
          return `
          <div class="widget-container">
            <h3>${widget.title}</h3>
            <p>Widget content would appear here</p>
            ${widget.description ? `<p><small>${widget.description}</small></p>` : ''}
          </div>
        `;
      }
    })
    .join('\n');

  return `
    <div class="dashboard">
      <h1>${dashboard.name}</h1>
      ${dashboard.description ? `<p>${dashboard.description}</p>` : ''}
      <hr>
      <div class="widgets">
        ${widgetHtml}
      </div>
      <hr>
      <p><small>Generated on ${new Date().toLocaleString()}</small></p>
    </div>
  `;
};

// Data formatting utilities for exports
export const formatDataForExport = (
  data: any[],
  options: {
    dateFormat?: 'iso' | 'local' | 'short';
    numberFormat?: 'decimal' | 'scientific' | 'percentage';
    includeMetadata?: boolean;
  } = {}
): any[] => {
  const { dateFormat = 'iso', numberFormat = 'decimal', includeMetadata = false } = options;

  return data.map((item) => {
    const formatted: any = {};

    for (const [key, value] of Object.entries(item)) {
      if (key === 'metadata' && !includeMetadata) {
        continue;
      }

      if (value instanceof Date) {
        switch (dateFormat) {
          case 'iso':
            formatted[key] = value.toISOString();
            break;
          case 'local':
            formatted[key] = value.toLocaleString();
            break;
          case 'short':
            formatted[key] = value.toLocaleDateString();
            break;
          default:
            formatted[key] = value.toISOString();
        }
      } else if (typeof value === 'number') {
        switch (numberFormat) {
          case 'scientific':
            formatted[key] = value.toExponential();
            break;
          case 'percentage':
            formatted[key] = (value * 100).toFixed(2) + '%';
            break;
          case 'decimal':
          default:
            formatted[key] = value;
        }
      } else if (typeof value === 'object' && value !== null) {
        // Flatten objects or convert to JSON string
        if (includeMetadata || key !== 'metadata') {
          formatted[key] = JSON.stringify(value);
        }
      } else {
        formatted[key] = value;
      }
    }

    return formatted;
  });
};
