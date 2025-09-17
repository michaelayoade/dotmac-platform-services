import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  ScatterChart,
  Scatter,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { cn } from '@dotmac/primitives/utils/cn';
import type { ChartWidgetProps, TimeSeries } from '../../types';

const DEFAULT_COLORS = [
  '#3B82F6',
  '#EF4444',
  '#10B981',
  '#F59E0B',
  '#8B5CF6',
  '#F97316',
  '#06B6D4',
  '#84CC16',
  '#EC4899',
  '#6B7280',
];

const formatAxisValue = (value: any, format?: any) => {
  if (typeof value === 'number') {
    if (format?.currency) {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: format.currency,
        notation: 'compact',
      }).format(value);
    }

    if (format?.percentage) {
      return `${(value * 100).toFixed(1)}%`;
    }

    return new Intl.NumberFormat('en-US', { notation: 'compact' }).format(value);
  }

  if (value instanceof Date) {
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      ...(format?.showTime && { hour: 'numeric', minute: '2-digit' }),
    }).format(value);
  }

  return value;
};

const CustomTooltip = ({ active, payload, label, config }: any) => {
  if (!active || !payload || !payload.length) return null;

  return (
    <div className='bg-white p-3 border rounded-lg shadow-lg'>
      <p className='font-medium text-gray-900 mb-2'>{formatAxisValue(label, config?.formatting)}</p>
      {payload.map((entry: any, index: number) => (
        <div key={index} className='flex items-center space-x-2 text-sm'>
          <div className='w-3 h-3 rounded-full' style={{ backgroundColor: entry.color }} />
          <span className='text-gray-600'>{entry.name}:</span>
          <span className='font-medium text-gray-900'>
            {formatAxisValue(entry.value, config?.formatting)}
          </span>
        </div>
      ))}
    </div>
  );
};

export const ChartWidget: React.FC<ChartWidgetProps> = ({
  widget,
  data = [],
  isLoading = false,
  error = null,
  onRefresh,
  onEdit,
  className,
}) => {
  const [chartData, setChartData] = useState<any[]>([]);

  useEffect(() => {
    if (data && data.length > 0) {
      // Transform TimeSeries data to chart format
      const transformedData =
        data[0]?.data.map((point) => ({
          timestamp: point.timestamp,
          ...data.reduce(
            (acc, series, index) => {
              const seriesName = series.metricId || `Series ${index + 1}`;
              const dataPoint = series.data.find(
                (d) => d.timestamp.getTime() === point.timestamp.getTime()
              );
              acc[seriesName] = dataPoint?.value || 0;
              return acc;
            },
            {} as Record<string, number>
          ),
        })) || [];

      setChartData(transformedData);
    }
  }, [data]);

  const renderChart = () => {
    const colors = widget.config.colorScheme || DEFAULT_COLORS;
    const chartProps = {
      data: chartData,
      margin: { top: 5, right: 30, left: 20, bottom: 5 },
    };

    switch (widget.config.chartType) {
      case 'area':
        return (
          <AreaChart {...chartProps}>
            <CartesianGrid strokeDasharray='3 3' className='opacity-30' />
            <XAxis
              dataKey='timestamp'
              tickFormatter={(value) => formatAxisValue(value, widget.config.formatting)}
            />
            <YAxis tickFormatter={(value) => formatAxisValue(value, widget.config.formatting)} />
            <Tooltip content={<CustomTooltip config={widget.config} />} />
            {widget.config.showLegend && <Legend />}
            {data.map((series, index) => (
              <Area
                key={series.metricId}
                type='monotone'
                dataKey={series.metricId}
                stackId={widget.config.aggregation?.groupBy ? '1' : undefined}
                stroke={colors[index % colors.length]}
                fill={colors[index % colors.length]}
                fillOpacity={0.6}
                name={series.metricId}
              />
            ))}
          </AreaChart>
        );

      case 'bar':
        return (
          <BarChart {...chartProps}>
            <CartesianGrid strokeDasharray='3 3' className='opacity-30' />
            <XAxis
              dataKey='timestamp'
              tickFormatter={(value) => formatAxisValue(value, widget.config.formatting)}
            />
            <YAxis tickFormatter={(value) => formatAxisValue(value, widget.config.formatting)} />
            <Tooltip content={<CustomTooltip config={widget.config} />} />
            {widget.config.showLegend && <Legend />}
            {data.map((series, index) => (
              <Bar
                key={series.metricId}
                dataKey={series.metricId}
                fill={colors[index % colors.length]}
                name={series.metricId}
              />
            ))}
          </BarChart>
        );

      case 'pie':
      case 'donut':
        const pieData = data.map((series, index) => ({
          name: series.metricId,
          value: series.data.reduce((sum, point) => sum + point.value, 0),
          fill: colors[index % colors.length],
        }));

        return (
          <PieChart {...chartProps}>
            <Pie
              data={pieData}
              cx='50%'
              cy='50%'
              innerRadius={widget.config.chartType === 'donut' ? 60 : 0}
              outerRadius={80}
              paddingAngle={5}
              dataKey='value'
            >
              {pieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip config={widget.config} />} />
            {widget.config.showLegend && <Legend />}
          </PieChart>
        );

      case 'scatter':
        return (
          <ScatterChart {...chartProps}>
            <CartesianGrid strokeDasharray='3 3' className='opacity-30' />
            <XAxis
              dataKey='timestamp'
              tickFormatter={(value) => formatAxisValue(value, widget.config.formatting)}
            />
            <YAxis tickFormatter={(value) => formatAxisValue(value, widget.config.formatting)} />
            <Tooltip content={<CustomTooltip config={widget.config} />} />
            {widget.config.showLegend && <Legend />}
            {data.map((series, index) => (
              <Scatter
                key={series.metricId}
                dataKey={series.metricId}
                fill={colors[index % colors.length]}
                name={series.metricId}
              />
            ))}
          </ScatterChart>
        );

      default: // line chart
        return (
          <LineChart {...chartProps}>
            <CartesianGrid strokeDasharray='3 3' className='opacity-30' />
            <XAxis
              dataKey='timestamp'
              tickFormatter={(value) => formatAxisValue(value, widget.config.formatting)}
            />
            <YAxis tickFormatter={(value) => formatAxisValue(value, widget.config.formatting)} />
            <Tooltip content={<CustomTooltip config={widget.config} />} />
            {widget.config.showLegend && <Legend />}
            {data.map((series, index) => (
              <Line
                key={series.metricId}
                type='monotone'
                dataKey={series.metricId}
                stroke={colors[index % colors.length]}
                strokeWidth={2}
                dot={false}
                name={series.metricId}
              />
            ))}
          </LineChart>
        );
    }
  };

  if (error) {
    return (
      <div className={cn('bg-white rounded-lg border p-6', className)}>
        <div className='text-center'>
          <div className='text-red-600 mb-2'>
            <svg className='w-8 h-8 mx-auto' fill='currentColor' viewBox='0 0 20 20'>
              <path
                fillRule='evenodd'
                d='M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z'
                clipRule='evenodd'
              />
            </svg>
          </div>
          <p className='text-gray-600'>{error}</p>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className='mt-2 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700'
            >
              Retry
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={cn('bg-white rounded-lg border overflow-hidden', className)}>
      {/* Widget Header */}
      <div className='flex items-center justify-between p-4 border-b bg-gray-50'>
        <div>
          <h3 className='font-medium text-gray-900'>{widget.title}</h3>
          {widget.description && <p className='text-sm text-gray-500'>{widget.description}</p>}
        </div>

        <div className='flex items-center space-x-2'>
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className='p-1 text-gray-500 hover:text-gray-700 disabled:opacity-50'
              title='Refresh'
            >
              <svg className='w-4 h-4' fill='currentColor' viewBox='0 0 20 20'>
                <path
                  fillRule='evenodd'
                  d='M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z'
                  clipRule='evenodd'
                />
              </svg>
            </button>
          )}

          {onEdit && (
            <button
              onClick={onEdit}
              className='p-1 text-gray-500 hover:text-gray-700'
              title='Edit widget'
            >
              <svg className='w-4 h-4' fill='currentColor' viewBox='0 0 20 20'>
                <path d='M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z' />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Chart Content */}
      <div className='p-4'>
        {isLoading ? (
          <div className='flex items-center justify-center h-64'>
            <div className='animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600'></div>
            <span className='ml-2 text-gray-600'>Loading chart...</span>
          </div>
        ) : chartData.length === 0 ? (
          <div className='flex items-center justify-center h-64 text-gray-500'>
            <div className='text-center'>
              <svg
                className='w-12 h-12 mx-auto mb-4 text-gray-300'
                fill='currentColor'
                viewBox='0 0 20 20'
              >
                <path
                  fillRule='evenodd'
                  d='M5 3a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2V5a2 2 0 00-2-2H5zm0 2h10v7h-2l-1-2H9l-1 2H6V5z'
                  clipRule='evenodd'
                />
              </svg>
              <p>No data available</p>
            </div>
          </div>
        ) : (
          <ResponsiveContainer width='100%' height={300}>
            {renderChart()}
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};
