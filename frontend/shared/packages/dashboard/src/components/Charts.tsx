/**
 * Universal Chart Components
 * Consistent chart patterns across all portals
 */

import React from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { ChartData, PortalType } from '../types';

const PORTAL_COLORS = {
  admin: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'],
  customer: ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6'],
  reseller: ['#8B5CF6', '#3B82F6', '#10B981', '#F59E0B', '#EF4444'],
  technician: ['#F97316', '#3B82F6', '#10B981', '#F59E0B', '#EF4444'],
  management: ['#EF4444', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6'],
};

interface BaseChartProps {
  data: ChartData[];
  portal?: PortalType;
  height?: number;
  showLegend?: boolean;
}

interface LineChartProps extends BaseChartProps {
  dataKey: string;
  strokeColor?: string;
  showDots?: boolean;
}

interface AreaChartProps extends BaseChartProps {
  dataKey: string;
  fillColor?: string;
  strokeColor?: string;
}

interface BarChartProps extends BaseChartProps {
  dataKey: string;
  fillColor?: string;
}

interface PieChartProps extends BaseChartProps {
  dataKey: string;
  nameKey?: string;
  showLabels?: boolean;
}

export function UniversalLineChart({
  data,
  dataKey,
  portal = 'admin',
  height = 300,
  strokeColor,
  showDots = true,
  showLegend = true,
}: LineChartProps) {
  const colors = PORTAL_COLORS[portal];
  const stroke = strokeColor || colors[0];

  return (
    <ResponsiveContainer width='100%' height={height}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray='3 3' stroke='#E5E7EB' />
        <XAxis dataKey='name' stroke='#6B7280' fontSize={12} />
        <YAxis stroke='#6B7280' fontSize={12} />
        <Tooltip
          contentStyle={{
            backgroundColor: '#FFFFFF',
            border: '1px solid #E5E7EB',
            borderRadius: '8px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          }}
        />
        {showLegend && <Legend />}
        <Line
          type='monotone'
          dataKey={dataKey}
          stroke={stroke}
          strokeWidth={2}
          dot={showDots ? { fill: stroke, strokeWidth: 2, r: 4 } : false}
          activeDot={{ r: 6, fill: stroke }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function UniversalAreaChart({
  data,
  dataKey,
  portal = 'admin',
  height = 300,
  fillColor,
  strokeColor,
  showLegend = true,
}: AreaChartProps) {
  const colors = PORTAL_COLORS[portal];
  const fill = fillColor || colors[0];
  const stroke = strokeColor || colors[0];

  return (
    <ResponsiveContainer width='100%' height={height}>
      <AreaChart data={data}>
        <CartesianGrid strokeDasharray='3 3' stroke='#E5E7EB' />
        <XAxis dataKey='name' stroke='#6B7280' fontSize={12} />
        <YAxis stroke='#6B7280' fontSize={12} />
        <Tooltip
          contentStyle={{
            backgroundColor: '#FFFFFF',
            border: '1px solid #E5E7EB',
            borderRadius: '8px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          }}
        />
        {showLegend && <Legend />}
        <Area type='monotone' dataKey={dataKey} stroke={stroke} fill={fill} fillOpacity={0.6} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function UniversalBarChart({
  data,
  dataKey,
  portal = 'admin',
  height = 300,
  fillColor,
  showLegend = true,
}: BarChartProps) {
  const colors = PORTAL_COLORS[portal];
  const fill = fillColor || colors[0];

  return (
    <ResponsiveContainer width='100%' height={height}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray='3 3' stroke='#E5E7EB' />
        <XAxis dataKey='name' stroke='#6B7280' fontSize={12} />
        <YAxis stroke='#6B7280' fontSize={12} />
        <Tooltip
          contentStyle={{
            backgroundColor: '#FFFFFF',
            border: '1px solid #E5E7EB',
            borderRadius: '8px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          }}
        />
        {showLegend && <Legend />}
        <Bar dataKey={dataKey} fill={fill} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function UniversalPieChart({
  data,
  dataKey,
  nameKey = 'name',
  portal = 'admin',
  height = 300,
  showLabels = true,
}: PieChartProps) {
  const colors = PORTAL_COLORS[portal];

  return (
    <ResponsiveContainer width='100%' height={height}>
      <PieChart>
        <Pie
          data={data}
          dataKey={dataKey}
          nameKey={nameKey}
          cx='50%'
          cy='50%'
          outerRadius={Math.min(height * 0.35, 120)}
          label={showLabels}
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            backgroundColor: '#FFFFFF',
            border: '1px solid #E5E7EB',
            borderRadius: '8px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          }}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}

// Chart container with consistent styling
export function ChartContainer({
  title,
  children,
  className = '',
}: {
  title?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`bg-white p-6 rounded-lg shadow-sm border border-gray-200 ${className}`}>
      {title && <h3 className='text-lg font-semibold text-gray-900 mb-4'>{title}</h3>}
      {children}
    </div>
  );
}
