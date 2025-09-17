/**
 * Dashboard Types
 */

import { LucideIcon } from 'lucide-react';

export type PortalType = 'admin' | 'customer' | 'reseller' | 'technician' | 'management';

export interface MetricData {
  name: string;
  value: string | number;
  total?: string | number;
  icon: LucideIcon;
  trend?: {
    value: string;
    positive: boolean;
  };
  description?: string;
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'danger';
  link?: string;
}

export interface ChartData {
  name: string;
  value: number;
  [key: string]: any;
}

export interface TableColumn {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (value: any, row: any) => React.ReactNode;
  width?: string;
}

export interface DashboardConfig {
  portal: PortalType;
  title?: string;
  showHeader?: boolean;
  showSidebar?: boolean;
  gridColumns?: 2 | 3 | 4 | 6;
  theme?: 'light' | 'dark';
  customColors?: Record<string, string>;
}

export interface FilterOption {
  label: string;
  value: string;
  type: 'select' | 'date' | 'text' | 'number';
  options?: { label: string; value: string }[];
}

export interface SearchAndFilterProps {
  searchPlaceholder?: string;
  filters?: FilterOption[];
  onSearch?: (query: string) => void;
  onFilter?: (filters: Record<string, any>) => void;
  showExport?: boolean;
  onExport?: () => void;
}
