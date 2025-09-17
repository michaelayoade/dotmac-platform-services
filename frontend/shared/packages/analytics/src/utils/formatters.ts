import type { MetricDefinition } from '../types';

export const formatMetricValue = (
  value: number,
  definition: Pick<MetricDefinition, 'unit' | 'format'> | { unit?: string; format?: any }
): string => {
  if (definition.format?.currency) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: definition.format.currency,
      minimumFractionDigits: definition.format.decimals || 0,
      maximumFractionDigits: definition.format.decimals || 2,
    }).format(value);
  }

  if (definition.format?.percentage) {
    return new Intl.NumberFormat('en-US', {
      style: 'percent',
      minimumFractionDigits: definition.format.decimals || 1,
      maximumFractionDigits: definition.format.decimals || 2,
    }).format(value);
  }

  let formatted = new Intl.NumberFormat('en-US', {
    minimumFractionDigits: definition.format?.decimals || 0,
    maximumFractionDigits: definition.format?.decimals || 2,
  }).format(value);

  if (definition.format?.prefix) {
    formatted = definition.format.prefix + formatted;
  }

  if (definition.format?.suffix) {
    formatted = formatted + definition.format.suffix;
  }

  if (definition.unit && !definition.format?.prefix && !definition.format?.suffix) {
    formatted = formatted + ' ' + definition.unit;
  }

  return formatted;
};

export const formatNumber = (
  value: number,
  options: {
    decimals?: number;
    compact?: boolean;
    currency?: string;
    percentage?: boolean;
    prefix?: string;
    suffix?: string;
  } = {}
): string => {
  const { decimals = 0, compact = false, currency, percentage = false, prefix, suffix } = options;

  let formatOptions: Intl.NumberFormatOptions = {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  };

  if (compact) {
    formatOptions.notation = 'compact';
  }

  if (currency) {
    formatOptions.style = 'currency';
    formatOptions.currency = currency;
  }

  if (percentage) {
    formatOptions.style = 'percent';
  }

  let formatted = new Intl.NumberFormat('en-US', formatOptions).format(percentage ? value : value);

  if (prefix) formatted = prefix + formatted;
  if (suffix) formatted = formatted + suffix;

  return formatted;
};

export const formatBytes = (bytes: number, decimals = 2): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
};

export const formatDuration = (milliseconds: number): string => {
  const seconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return `${days}d ${hours % 24}h ${minutes % 60}m`;
  } else if (hours > 0) {
    return `${hours}h ${minutes % 60}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`;
  } else {
    return `${seconds}s`;
  }
};

export const formatDate = (
  date: Date,
  options: {
    includeTime?: boolean;
    relative?: boolean;
    format?: 'short' | 'medium' | 'long' | 'full';
  } = {}
): string => {
  const { includeTime = false, relative = false, format = 'medium' } = options;

  if (relative) {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return 'Today';
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else if (diffDays < 30) {
      const weeks = Math.floor(diffDays / 7);
      return `${weeks} week${weeks > 1 ? 's' : ''} ago`;
    } else if (diffDays < 365) {
      const months = Math.floor(diffDays / 30);
      return `${months} month${months > 1 ? 's' : ''} ago`;
    } else {
      const years = Math.floor(diffDays / 365);
      return `${years} year${years > 1 ? 's' : ''} ago`;
    }
  }

  const dateFormatOptions: Intl.DateTimeFormatOptions = {
    dateStyle: format,
  };

  if (includeTime) {
    dateFormatOptions.timeStyle = 'short';
  }

  return new Intl.DateTimeFormat('en-US', dateFormatOptions).format(date);
};

export const formatPercentage = (value: number, decimals = 1): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

export const formatChangeIndicator = (
  current: number,
  previous: number,
  options: {
    showSign?: boolean;
    showPercentage?: boolean;
    showArrow?: boolean;
    decimals?: number;
  } = {}
): {
  value: string;
  trend: 'up' | 'down' | 'stable';
  percentage: number;
} => {
  const { showSign = true, showPercentage = true, showArrow = false, decimals = 1 } = options;

  const difference = current - previous;
  const percentage = previous !== 0 ? difference / previous : 0;

  let trend: 'up' | 'down' | 'stable';
  if (Math.abs(percentage) < 0.001) {
    // Less than 0.1% change
    trend = 'stable';
  } else if (difference > 0) {
    trend = 'up';
  } else {
    trend = 'down';
  }

  let value = '';

  if (showArrow) {
    if (trend === 'up') value += '↗ ';
    else if (trend === 'down') value += '↘ ';
    else value += '→ ';
  }

  if (showSign && trend !== 'stable') {
    value += difference > 0 ? '+' : '';
  }

  if (showPercentage) {
    value += formatPercentage(Math.abs(percentage), decimals);
  } else {
    value += formatNumber(Math.abs(difference), { decimals });
  }

  return { value, trend, percentage };
};
