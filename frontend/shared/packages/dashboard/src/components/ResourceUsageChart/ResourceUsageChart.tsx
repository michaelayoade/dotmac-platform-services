/**
 * Universal ResourceUsageChart Component
 * Production-ready, portal-agnostic resource monitoring
 * DRY pattern: Same chart, different metrics across all portals
 */

import React, { useState, useMemo } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { motion } from 'framer-motion';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from 'recharts';
import {
  Cpu,
  HardDrive,
  Wifi,
  MemoryStick,
  TrendingUp,
  AlertTriangle,
  Calendar,
  Download,
} from 'lucide-react';
import { Card, Button } from '@dotmac/primitives';
import type { ResourceMetrics, PortalVariant, ChartTimeframe } from '../../types';
import { cn } from '../../utils/cn';
import { format, subHours, subDays, subWeeks } from 'date-fns';

const chartVariants = cva('w-full', {
  variants: {
    variant: {
      admin: 'border-blue-200',
      customer: 'border-green-200',
      reseller: 'border-purple-200',
      technician: 'border-orange-200',
      management: 'border-indigo-200',
    },
    chartType: {
      line: '',
      area: 'bg-gradient-to-t from-gray-50 to-white',
    },
  },
});

const getPortalColors = (variant: PortalVariant) => {
  const colorMap = {
    admin: {
      primary: '#3B82F6',
      secondary: '#60A5FA',
      background: '#EFF6FF',
      text: '#1E40AF',
    },
    customer: {
      primary: '#10B981',
      secondary: '#34D399',
      background: '#ECFDF5',
      text: '#047857',
    },
    reseller: {
      primary: '#8B5CF6',
      secondary: '#A78BFA',
      background: '#F5F3FF',
      text: '#7C3AED',
    },
    technician: {
      primary: '#F59E0B',
      secondary: '#FBBF24',
      background: '#FFFBEB',
      text: '#D97706',
    },
    management: {
      primary: '#6366F1',
      secondary: '#818CF8',
      background: '#EEF2FF',
      text: '#4F46E5',
    },
  };

  return colorMap[variant];
};

const timeframes: ChartTimeframe[] = [
  { label: '1 Hour', value: '1h', hours: 1 },
  { label: '6 Hours', value: '6h', hours: 6 },
  { label: '24 Hours', value: '24h', hours: 24 },
  { label: '7 Days', value: '7d', hours: 168 },
  { label: '30 Days', value: '30d', hours: 720 },
];

const resourceIcons = {
  cpu: Cpu,
  memory: MemoryStick,
  storage: HardDrive,
  bandwidth: Wifi,
};

export interface ResourceUsageChartProps extends VariantProps<typeof chartVariants> {
  metrics: ResourceMetrics;
  variant: PortalVariant;
  timeframe?: string;
  chartType?: 'line' | 'area';
  showLegend?: boolean;
  showGrid?: boolean;
  height?: number;
  className?: string;
  onTimeframeChange?: (timeframe: string) => void;
  onExport?: (data: any[]) => void;
}

export const ResourceUsageChart: React.FC<ResourceUsageChartProps> = ({
  metrics,
  variant,
  timeframe = '24h',
  chartType = 'area',
  showLegend = true,
  showGrid = true,
  height = 300,
  className,
  onTimeframeChange,
  onExport,
  ...props
}) => {
  const [selectedMetrics, setSelectedMetrics] = useState<Set<string>>(
    new Set(['cpu', 'memory', 'storage', 'bandwidth'])
  );

  const colors = getPortalColors(variant);

  const chartData = useMemo(() => {
    // Find the longest history array
    const allHistories = [
      metrics.cpu.history,
      metrics.memory.history,
      metrics.storage.history,
      metrics.bandwidth.history,
    ];

    const maxLength = Math.max(...allHistories.map((h) => h.length));
    if (maxLength === 0) return [];

    // Create unified data points
    const data: any[] = [];

    for (let i = 0; i < maxLength; i++) {
      const timestamp = allHistories.find((h) => h[i])?.at(i)?.timestamp || new Date();

      data.push({
        timestamp: timestamp.getTime(),
        formattedTime: format(timestamp, 'HH:mm'),
        formattedDate: format(timestamp, 'MMM dd'),
        cpu: metrics.cpu.history[i]?.value || 0,
        memory: metrics.memory.history[i]?.value || 0,
        storage: metrics.storage.history[i]?.value || 0,
        bandwidth: metrics.bandwidth.history[i]?.value || 0,
      });
    }

    return data.sort((a, b) => a.timestamp - b.timestamp);
  }, [metrics]);

  const currentValues = {
    cpu: metrics.cpu.current,
    memory: metrics.memory.current,
    storage: metrics.storage.current,
    bandwidth: metrics.bandwidth.current,
  };

  const getResourceStatus = (value: number, type: string) => {
    const thresholds = {
      cpu: { warning: 70, critical: 90 },
      memory: { warning: 80, critical: 95 },
      storage: { warning: 85, critical: 95 },
      bandwidth: { warning: 70, critical: 85 },
    };

    const threshold = thresholds[type as keyof typeof thresholds] || { warning: 80, critical: 90 };

    if (value >= threshold.critical) return 'critical';
    if (value >= threshold.warning) return 'warning';
    return 'normal';
  };

  const toggleMetric = (metric: string) => {
    const newSelected = new Set(selectedMetrics);
    if (newSelected.has(metric)) {
      newSelected.delete(metric);
    } else {
      newSelected.add(metric);
    }
    setSelectedMetrics(newSelected);
  };

  const ResourceSummaryCard = ({
    type,
    value,
    label,
  }: {
    type: string;
    value: number;
    label: string;
  }) => {
    const Icon = resourceIcons[type as keyof typeof resourceIcons];
    const status = getResourceStatus(value, type);
    const isSelected = selectedMetrics.has(type);

    return (
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => toggleMetric(type)}
        className={cn(
          'p-3 rounded-lg border-2 transition-all text-left w-full',
          isSelected
            ? 'border-current bg-current/5'
            : 'border-gray-200 bg-white hover:border-gray-300',
          status === 'critical' && 'text-red-600',
          status === 'warning' && 'text-yellow-600',
          status === 'normal' && 'text-gray-700'
        )}
        style={{
          borderColor: isSelected ? colors.primary : undefined,
          color: isSelected ? colors.text : undefined,
        }}
      >
        <div className='flex items-center justify-between mb-2'>
          <Icon size={16} />
          {status !== 'normal' && (
            <AlertTriangle
              size={12}
              className={status === 'critical' ? 'text-red-500' : 'text-yellow-500'}
            />
          )}
        </div>
        <div className='text-lg font-semibold'>{value}%</div>
        <div className='text-xs text-gray-500'>{label}</div>
      </motion.button>
    );
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className='bg-white p-3 border border-gray-200 rounded-lg shadow-lg'>
          <p className='text-sm font-medium text-gray-900 mb-2'>
            {format(new Date(label), 'MMM dd, HH:mm')}
          </p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className='text-sm' style={{ color: entry.color }}>
              {entry.name}: {entry.value}%
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <Card className={cn(chartVariants({ variant, chartType }), className)} {...props}>
      {/* Header */}
      <div className='p-4 border-b border-gray-200'>
        <div className='flex items-center justify-between mb-4'>
          <h3 className='text-lg font-semibold text-gray-900 flex items-center gap-2'>
            <TrendingUp size={20} style={{ color: colors.primary }} />
            Resource Usage
          </h3>

          <div className='flex items-center gap-2'>
            {onExport && (
              <Button
                variant='ghost'
                size='sm'
                onClick={() => onExport(chartData)}
                className='h-8 px-3'
              >
                <Download size={14} className='mr-1' />
                Export
              </Button>
            )}

            <select
              value={timeframe}
              onChange={(e) => onTimeframeChange?.(e.target.value)}
              className='h-8 px-3 text-sm border border-gray-300 rounded-md bg-white'
            >
              {timeframes.map((tf) => (
                <option key={tf.value} value={tf.value}>
                  {tf.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Resource Summary */}
        <div className='grid grid-cols-4 gap-3'>
          <ResourceSummaryCard type='cpu' value={currentValues.cpu} label='CPU' />
          <ResourceSummaryCard type='memory' value={currentValues.memory} label='Memory' />
          <ResourceSummaryCard type='storage' value={currentValues.storage} label='Storage' />
          <ResourceSummaryCard type='bandwidth' value={currentValues.bandwidth} label='Bandwidth' />
        </div>
      </div>

      {/* Chart */}
      <div className='p-4' style={{ height }}>
        {chartData.length === 0 ? (
          <div className='h-full flex items-center justify-center text-gray-500'>
            <div className='text-center'>
              <Calendar size={24} className='mx-auto mb-2 opacity-50' />
              <p>No data available for selected timeframe</p>
            </div>
          </div>
        ) : (
          <ResponsiveContainer width='100%' height='100%'>
            {chartType === 'area' ? (
              <AreaChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                {showGrid && <CartesianGrid strokeDasharray='3 3' stroke='#f0f0f0' />}
                <XAxis dataKey='formattedTime' stroke='#666' fontSize={12} />
                <YAxis domain={[0, 100]} stroke='#666' fontSize={12} />
                <Tooltip content={<CustomTooltip />} />
                {showLegend && <Legend />}

                {/* Reference lines for thresholds */}
                <ReferenceLine y={90} stroke='#ef4444' strokeDasharray='2 2' strokeOpacity={0.5} />
                <ReferenceLine y={80} stroke='#f59e0b' strokeDasharray='2 2' strokeOpacity={0.5} />

                {selectedMetrics.has('cpu') && (
                  <Area
                    type='monotone'
                    dataKey='cpu'
                    stackId='1'
                    stroke={colors.primary}
                    fill={colors.primary}
                    fillOpacity={0.3}
                    name='CPU'
                  />
                )}
                {selectedMetrics.has('memory') && (
                  <Area
                    type='monotone'
                    dataKey='memory'
                    stackId='1'
                    stroke='#10B981'
                    fill='#10B981'
                    fillOpacity={0.3}
                    name='Memory'
                  />
                )}
                {selectedMetrics.has('storage') && (
                  <Area
                    type='monotone'
                    dataKey='storage'
                    stackId='1'
                    stroke='#F59E0B'
                    fill='#F59E0B'
                    fillOpacity={0.3}
                    name='Storage'
                  />
                )}
                {selectedMetrics.has('bandwidth') && (
                  <Area
                    type='monotone'
                    dataKey='bandwidth'
                    stackId='1'
                    stroke='#EF4444'
                    fill='#EF4444'
                    fillOpacity={0.3}
                    name='Bandwidth'
                  />
                )}
              </AreaChart>
            ) : (
              <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                {showGrid && <CartesianGrid strokeDasharray='3 3' stroke='#f0f0f0' />}
                <XAxis dataKey='formattedTime' stroke='#666' fontSize={12} />
                <YAxis domain={[0, 100]} stroke='#666' fontSize={12} />
                <Tooltip content={<CustomTooltip />} />
                {showLegend && <Legend />}

                <ReferenceLine y={90} stroke='#ef4444' strokeDasharray='2 2' strokeOpacity={0.5} />
                <ReferenceLine y={80} stroke='#f59e0b' strokeDasharray='2 2' strokeOpacity={0.5} />

                {selectedMetrics.has('cpu') && (
                  <Line
                    type='monotone'
                    dataKey='cpu'
                    stroke={colors.primary}
                    strokeWidth={2}
                    dot={false}
                    name='CPU'
                  />
                )}
                {selectedMetrics.has('memory') && (
                  <Line
                    type='monotone'
                    dataKey='memory'
                    stroke='#10B981'
                    strokeWidth={2}
                    dot={false}
                    name='Memory'
                  />
                )}
                {selectedMetrics.has('storage') && (
                  <Line
                    type='monotone'
                    dataKey='storage'
                    stroke='#F59E0B'
                    strokeWidth={2}
                    dot={false}
                    name='Storage'
                  />
                )}
                {selectedMetrics.has('bandwidth') && (
                  <Line
                    type='monotone'
                    dataKey='bandwidth'
                    stroke='#EF4444'
                    strokeWidth={2}
                    dot={false}
                    name='Bandwidth'
                  />
                )}
              </LineChart>
            )}
          </ResponsiveContainer>
        )}
      </div>

      {/* Footer Info */}
      <div className='px-4 py-3 border-t border-gray-200 bg-gray-50'>
        <div className='flex items-center justify-between text-xs text-gray-600'>
          <span>Click metrics above to toggle visibility</span>
          <span>Last updated: {format(new Date(), 'HH:mm:ss')}</span>
        </div>
      </div>
    </Card>
  );
};

// Portal-specific metric generators
// DRY Resource Metrics Factory
export const createResourceMetric = (current: number, hours = 24, variance = 20) => ({
  current,
  history: Array.from({ length: hours }, (_, i) => ({
    timestamp: subHours(new Date(), hours - 1 - i),
    value: Math.max(0, current + (Math.random() - 0.5) * variance),
  })),
});

export const createResourceMetrics = (values: {
  cpu: number;
  memory: number;
  storage: number;
  bandwidth: number;
}): ResourceMetrics => ({
  cpu: createResourceMetric(values.cpu, 24, 20),
  memory: createResourceMetric(values.memory, 24, 15),
  storage: createResourceMetric(values.storage, 24, 10),
  bandwidth: createResourceMetric(values.bandwidth, 24, 30),
});

// Common resource configurations (DRY approach)
export const RESOURCE_CONFIGS = {
  platform: { cpu: 65, memory: 72, storage: 45, bandwidth: 80 },
  tenant: { cpu: 45, memory: 60, storage: 30, bandwidth: 55 },
  network: { cpu: 85, memory: 78, storage: 60, bandwidth: 95 },
  server: { cpu: 55, memory: 85, storage: 70, bandwidth: 40 },
} as const;

// Portal-specific preset aliases (leverages existing patterns)
export const ResourceUsagePresets = {
  management: RESOURCE_CONFIGS,
  admin: RESOURCE_CONFIGS,
  customer: RESOURCE_CONFIGS,
  reseller: RESOURCE_CONFIGS,
  technician: RESOURCE_CONFIGS,
} as const;
