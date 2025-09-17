import React, { useEffect, useState } from 'react';
import { cn } from '@dotmac/primitives/utils/cn';
import { UniversalLayout } from '@dotmac/primitives/layout';
import { useAnalytics } from '../../hooks/useAnalytics';
import { ChartWidget } from '../charts/ChartWidget';
import { MetricCard } from '../metrics/MetricCard';
import { FilterBar } from '../filters/FilterBar';
import { ExportButton } from '../export/ExportButton';
import { RealTimeIndicator } from '../realtime/RealTimeIndicator';
import type { AnalyticsDashboardProps, DashboardWidget, FilterConfig } from '../../types';

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({
  dashboardId,
  isReadOnly = false,
  theme = 'auto',
  height = '100vh',
  className,
  onWidgetClick,
  onError,
}) => {
  const {
    currentDashboard,
    isLoading,
    error,
    actions: { refresh, updateWidget },
  } = useAnalytics();

  const [appliedFilters, setAppliedFilters] = useState<Record<string, any>>({});
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (error && onError) {
      onError(error);
    }
  }, [error, onError]);

  const handleFilterChange = (filterId: string, value: any) => {
    setAppliedFilters((prev) => ({
      ...prev,
      [filterId]: value,
    }));
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refresh();
    } catch (err) {
      onError?.(err instanceof Error ? err.message : 'Failed to refresh dashboard');
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleWidgetUpdate = async (widgetId: string, updates: Partial<DashboardWidget>) => {
    if (!currentDashboard || isReadOnly) return;

    try {
      await updateWidget(currentDashboard.id, widgetId, updates);
    } catch (err) {
      onError?.(err instanceof Error ? err.message : 'Failed to update widget');
    }
  };

  if (isLoading) {
    return (
      <div className='flex items-center justify-center h-64'>
        <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600'></div>
        <span className='ml-2 text-gray-600'>Loading dashboard...</span>
      </div>
    );
  }

  if (!currentDashboard) {
    return (
      <div className='text-center text-gray-500 p-8'>
        <p>No dashboard selected</p>
      </div>
    );
  }

  const renderWidget = (widget: DashboardWidget) => {
    const commonProps = {
      widget,
      isLoading: isRefreshing,
      onRefresh: handleRefresh,
      onEdit: isReadOnly ? undefined : () => handleWidgetUpdate(widget.id, {}),
      onClick: () => onWidgetClick?.(widget),
      className: 'w-full h-full',
    };

    switch (widget.type) {
      case 'metric':
      case 'kpi':
        return <MetricCard {...commonProps} />;
      case 'chart':
        return <ChartWidget {...commonProps} />;
      default:
        return (
          <div className='p-4 border rounded-lg bg-gray-50'>
            <p className='text-gray-500'>Unsupported widget type: {widget.type}</p>
          </div>
        );
    }
  };

  return (
    <UniversalLayout
      className={cn('analytics-dashboard', className)}
      style={{ height }}
      data-theme={theme}
    >
      <div className='flex flex-col h-full'>
        {/* Dashboard Header */}
        <div className='flex items-center justify-between p-4 border-b bg-white'>
          <div className='flex items-center space-x-4'>
            <h1 className='text-2xl font-semibold text-gray-900'>{currentDashboard.name}</h1>
            {currentDashboard.description && (
              <p className='text-sm text-gray-500'>{currentDashboard.description}</p>
            )}
            <RealTimeIndicator isConnected={true} lastUpdate={new Date()} />
          </div>

          <div className='flex items-center space-x-2'>
            <ExportButton dashboardId={currentDashboard.id} disabled={isRefreshing} />
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className='px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50'
            >
              {isRefreshing ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
        </div>

        {/* Filters */}
        <FilterBar
          filters={currentDashboard.widgets
            .flatMap((w) => w.filters || [])
            .filter((filter, index, self) => self.findIndex((f) => f.id === filter.id) === index)}
          values={appliedFilters}
          onChange={handleFilterChange}
          className='p-4 bg-gray-50 border-b'
        />

        {/* Dashboard Grid */}
        <div className='flex-1 p-4 overflow-auto'>
          {currentDashboard.layout === 'grid' ? (
            <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4'>
              {currentDashboard.widgets
                .filter((widget) => widget.isVisible)
                .map((widget) => (
                  <div
                    key={widget.id}
                    className='min-h-64'
                    style={{
                      gridColumn: `span ${widget.position.width}`,
                      gridRow: `span ${widget.position.height}`,
                    }}
                  >
                    {renderWidget(widget)}
                  </div>
                ))}
            </div>
          ) : (
            <div className='space-y-4'>
              {currentDashboard.widgets
                .filter((widget) => widget.isVisible)
                .sort((a, b) => a.position.y - b.position.y || a.position.x - b.position.x)
                .map((widget) => (
                  <div key={widget.id} className='w-full'>
                    {renderWidget(widget)}
                  </div>
                ))}
            </div>
          )}
        </div>
      </div>
    </UniversalLayout>
  );
};
