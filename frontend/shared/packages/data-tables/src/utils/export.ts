/**
 * Universal Data Export Utilities
 * Supports CSV, XLSX, JSON, and PDF export with portal theming
 */

import type { ExportConfig, PortalVariant } from '../types';

// CSV Export
export const exportToCSV = <TData = any>(
  data: TData[],
  config: ExportConfig,
  filename?: string
): void => {
  const { includeHeaders = true, customFields, selectedOnly = false } = config;

  if (!data.length) {
    throw new Error('No data to export');
  }

  // Determine fields to export
  const fields = customFields || Object.keys(data[0] as any);

  // Generate CSV content
  let csvContent = '';

  // Add headers if enabled
  if (includeHeaders) {
    const headers = fields
      .map((field) => (typeof field === 'object' ? field.label : String(field)))
      .join(',');
    csvContent += headers + '\n';
  }

  // Add data rows
  data.forEach((row) => {
    const values = fields
      .map((field) => {
        let value: any;

        if (typeof field === 'object') {
          value = field.accessor(row);
        } else {
          value = (row as any)[field];
        }

        // Handle different data types
        if (value === null || value === undefined) {
          return '';
        }

        if (typeof value === 'string') {
          // Escape quotes and wrap in quotes if contains comma, quote, or newline
          const escaped = value.replace(/"/g, '""');
          return /[",\n\r]/.test(escaped) ? `"${escaped}"` : escaped;
        }

        if (typeof value === 'object') {
          return `"${JSON.stringify(value).replace(/"/g, '""')}"`;
        }

        return String(value);
      })
      .join(',');

    csvContent += values + '\n';
  });

  // Create and trigger download
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename || `export_${new Date().toISOString().split('T')[0]}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
};

// JSON Export
export const exportToJSON = <TData = any>(
  data: TData[],
  config: ExportConfig,
  filename?: string
): void => {
  if (!data.length) {
    throw new Error('No data to export');
  }

  // Process data based on custom fields if provided
  let exportData = data;

  if (config.customFields) {
    exportData = data.map((row) => {
      const processedRow: any = {};
      config.customFields!.forEach((field) => {
        processedRow[field.key] = field.accessor(row);
      });
      return processedRow;
    });
  }

  const jsonContent = JSON.stringify(exportData, null, 2);

  const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = filename || `export_${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(link.href);
};

// XLSX Export (using dynamic import)
export const exportToXLSX = async <TData = any>(
  data: TData[],
  config: ExportConfig,
  filename?: string
): Promise<void> => {
  if (!data.length) {
    throw new Error('No data to export');
  }

  try {
    // Dynamic import to avoid bundle bloat
    const XLSX = await import('xlsx');

    // Process data for XLSX
    let exportData = data;

    if (config.customFields) {
      exportData = data.map((row) => {
        const processedRow: any = {};
        config.customFields!.forEach((field) => {
          processedRow[field.label] = field.accessor(row);
        });
        return processedRow;
      });
    }

    // Create workbook and worksheet
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(exportData);

    // Add worksheet to workbook
    XLSX.utils.book_append_sheet(wb, ws, 'Export');

    // Generate buffer and create blob
    const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
    const blob = new Blob([wbout], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    // Trigger download
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename || `export_${new Date().toISOString().split('T')[0]}.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
  } catch (error) {
    console.error('Failed to export to XLSX:', error);
    throw new Error('XLSX export failed. Please try CSV format instead.');
  }
};

// PDF Export with portal theming
export const exportToPDF = async <TData = any>(
  data: TData[],
  config: ExportConfig,
  filename?: string,
  options: {
    portal?: PortalVariant;
    title?: string;
    orientation?: 'portrait' | 'landscape';
    pageSize?: 'A4' | 'letter';
  } = {}
): Promise<void> => {
  if (!data.length) {
    throw new Error('No data to export');
  }

  try {
    // Dynamic imports to avoid bundle bloat
    const [jsPDF, autoTable] = await Promise.all([
      import('jspdf').then((m) => m.default),
      import('jspdf-autotable').then((m) => m.default),
    ]);

    const {
      portal = 'admin',
      title = 'Data Export',
      orientation = 'landscape',
      pageSize = 'A4',
    } = options;

    // Portal color schemes
    const portalColors = {
      admin: { primary: [59, 130, 246], secondary: [239, 246, 255] },
      customer: { primary: [34, 197, 94], secondary: [240, 253, 244] },
      reseller: { primary: [168, 85, 247], secondary: [250, 245, 255] },
      technician: { primary: [249, 115, 22], secondary: [255, 247, 237] },
      management: { primary: [239, 68, 68], secondary: [254, 242, 242] },
    };

    const colors = portalColors[portal];

    // Initialize PDF
    const doc = new (jsPDF as any)({
      orientation,
      unit: 'mm',
      format: pageSize,
    });

    // Add title
    doc.setFontSize(18);
    doc.setTextColor(colors.primary[0], colors.primary[1], colors.primary[2]);
    doc.text(title, 14, 22);

    // Add metadata
    doc.setFontSize(10);
    doc.setTextColor(100, 100, 100);
    doc.text(`Generated on: ${new Date().toLocaleString()}`, 14, 30);
    doc.text(`Total records: ${data.length}`, 14, 36);

    // Prepare table data
    const fields = config.customFields || Object.keys(data[0] as any);

    const headers = fields.map((field) =>
      typeof field === 'object' ? field.label : String(field)
    );

    const rows = data.map((row) =>
      fields.map((field) => {
        let value: any;

        if (typeof field === 'object') {
          value = field.accessor(row);
        } else {
          value = (row as any)[field];
        }

        // Format value for PDF
        if (value === null || value === undefined) {
          return '';
        }

        if (typeof value === 'object') {
          return JSON.stringify(value);
        }

        return String(value);
      })
    );

    // Generate table
    (doc as any).autoTable({
      head: [headers],
      body: rows,
      startY: 45,
      styles: {
        fontSize: 8,
        cellPadding: 2,
      },
      headStyles: {
        fillColor: colors.primary,
        textColor: [255, 255, 255],
        fontStyle: 'bold',
      },
      alternateRowStyles: {
        fillColor: colors.secondary,
      },
      margin: { top: 45, left: 14, right: 14, bottom: 14 },
    });

    // Save PDF
    const pdfFilename = filename || `export_${new Date().toISOString().split('T')[0]}.pdf`;
    doc.save(pdfFilename);
  } catch (error) {
    console.error('Failed to export to PDF:', error);
    throw new Error('PDF export failed. Please try CSV format instead.');
  }
};

// Main export function
export const exportData = async <TData = any>(
  format: 'csv' | 'xlsx' | 'json' | 'pdf',
  data: TData[],
  config: ExportConfig,
  options?: {
    portal?: PortalVariant;
    title?: string;
    orientation?: 'portrait' | 'landscape';
    pageSize?: 'A4' | 'letter';
  }
): Promise<void> => {
  if (!data.length) {
    throw new Error('No data to export');
  }

  // Generate filename
  const timestamp = new Date().toISOString().split('T')[0];
  const baseFilename =
    typeof config.filename === 'function'
      ? config.filename(data)
      : config.filename || `export_${timestamp}`;

  const filename = baseFilename.includes('.') ? baseFilename : `${baseFilename}.${format}`;

  try {
    switch (format) {
      case 'csv':
        exportToCSV(data, config, filename);
        break;

      case 'json':
        exportToJSON(data, config, filename);
        break;

      case 'xlsx':
        await exportToXLSX(data, config, filename);
        break;

      case 'pdf':
        await exportToPDF(data, config, filename, options);
        break;

      default:
        throw new Error(`Unsupported export format: ${format}`);
    }
  } catch (error) {
    console.error(`Export failed for format ${format}:`, error);
    throw error;
  }
};

// Utility function to detect optimal export format based on data size
export const getRecommendedExportFormat = <TData = any>(
  data: TData[],
  availableFormats: Array<'csv' | 'xlsx' | 'json' | 'pdf'>
): 'csv' | 'xlsx' | 'json' | 'pdf' => {
  const rowCount = data.length;
  const columnCount = data.length > 0 ? Object.keys(data[0] as any).length : 0;

  // For large datasets, recommend CSV for performance
  if (rowCount > 10000) {
    return availableFormats.includes('csv') ? 'csv' : availableFormats[0];
  }

  // For medium datasets with many columns, recommend XLSX
  if (rowCount > 1000 && columnCount > 10) {
    return availableFormats.includes('xlsx') ? 'xlsx' : 'csv';
  }

  // For small datasets that need formatting, recommend PDF
  if (rowCount <= 100 && availableFormats.includes('pdf')) {
    return 'pdf';
  }

  // Default to CSV for broad compatibility
  return availableFormats.includes('csv') ? 'csv' : availableFormats[0];
};
