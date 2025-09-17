import React, { useState } from 'react';
import { cn } from '@dotmac/primitives/utils/cn';
import { useAnalytics } from '../../hooks/useAnalytics';
import type { DataExport } from '../../types';

interface ExportButtonProps {
  dashboardId?: string;
  widgetId?: string;
  className?: string;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const EXPORT_FORMATS = [
  { value: 'pdf', label: 'PDF Report', icon: '📄' },
  { value: 'excel', label: 'Excel Spreadsheet', icon: '📊' },
  { value: 'csv', label: 'CSV Data', icon: '📋' },
  { value: 'json', label: 'JSON Data', icon: '🔗' },
] as const;

export const ExportButton: React.FC<ExportButtonProps> = ({
  dashboardId,
  widgetId,
  className,
  disabled = false,
  size = 'md',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<'pdf' | 'excel' | 'csv' | 'json'>('pdf');

  const {
    actions: { exportData },
  } = useAnalytics();

  const sizeClasses = {
    sm: 'px-2 py-1 text-sm',
    md: 'px-3 py-2 text-sm',
    lg: 'px-4 py-2 text-base',
  };

  const handleExport = async () => {
    if (!dashboardId && !widgetId) return;

    setIsExporting(true);
    try {
      const exportConfig: Omit<DataExport, 'id' | 'status' | 'requestedAt'> = {
        name: `Export-${new Date().toISOString().split('T')[0]}`,
        format: selectedFormat,
        dashboardId,
        dateRange: {
          start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // Last 30 days
          end: new Date(),
        },
        requestedBy: 'current-user', // This should come from auth context
      };

      const exportId = await exportData(exportConfig);

      // You might want to show a success message or handle the download
      console.log('Export initiated:', exportId);

      setIsOpen(false);
    } catch (error) {
      console.error('Export failed:', error);
      // Handle error - show toast notification
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className='relative'>
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || isExporting}
        className={cn(
          'inline-flex items-center border border-gray-300 rounded-md shadow-sm bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed',
          sizeClasses[size],
          className
        )}
      >
        <svg className='w-4 h-4 mr-2' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
          <path
            strokeLinecap='round'
            strokeLinejoin='round'
            strokeWidth={2}
            d='M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z'
          />
        </svg>
        {isExporting ? 'Exporting...' : 'Export'}
        <svg className='w-4 h-4 ml-1' fill='currentColor' viewBox='0 0 20 20'>
          <path
            fillRule='evenodd'
            d='M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z'
            clipRule='evenodd'
          />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className='absolute right-0 mt-2 w-64 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-50'>
          <div className='py-1'>
            <div className='px-4 py-2 border-b border-gray-100'>
              <h3 className='text-sm font-medium text-gray-900'>Export Options</h3>
            </div>

            {/* Format Selection */}
            <div className='px-4 py-3'>
              <label className='block text-xs font-medium text-gray-700 mb-2'>Format</label>
              <div className='space-y-2'>
                {EXPORT_FORMATS.map((format) => (
                  <label key={format.value} className='flex items-center'>
                    <input
                      type='radio'
                      name='export-format'
                      value={format.value}
                      checked={selectedFormat === format.value}
                      onChange={(e) => setSelectedFormat(e.target.value as any)}
                      className='h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300'
                    />
                    <span className='ml-3 flex items-center text-sm text-gray-700'>
                      <span className='mr-2'>{format.icon}</span>
                      {format.label}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Date Range - for future enhancement */}
            <div className='px-4 py-3 border-t border-gray-100'>
              <label className='block text-xs font-medium text-gray-700 mb-2'>Date Range</label>
              <select className='block w-full text-sm border-gray-300 rounded-md'>
                <option value='30d'>Last 30 days</option>
                <option value='7d'>Last 7 days</option>
                <option value='1d'>Last 24 hours</option>
                <option value='custom'>Custom range</option>
              </select>
            </div>

            {/* Action Buttons */}
            <div className='px-4 py-3 border-t border-gray-100 flex justify-end space-x-2'>
              <button
                onClick={() => setIsOpen(false)}
                className='px-3 py-1 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50'
              >
                Cancel
              </button>
              <button
                onClick={handleExport}
                disabled={isExporting}
                className='px-3 py-1 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50'
              >
                {isExporting ? 'Processing...' : 'Export'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Backdrop */}
      {isOpen && <div className='fixed inset-0 z-40' onClick={() => setIsOpen(false)} />}
    </div>
  );
};
