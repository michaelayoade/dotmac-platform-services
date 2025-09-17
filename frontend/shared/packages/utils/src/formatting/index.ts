/**
 * Common formatting utilities consolidated from multiple packages
 */

// Re-export cn utility from canonical source
export { cn } from '@dotmac/primitives/utils';

// File size formatting
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Currency formatting - Re-export from dedicated currency module
export {
  formatCurrency,
  formatCurrencyCompact,
  formatCurrencyNumeric,
  formatCurrencyWithSign,
  formatUSD,
  formatEUR,
  formatGBP,
  formatJPY,
  formatPluginPrice,
  getCurrencyInfo,
  isSupportedCurrency,
  getSupportedCurrencies,
  getCurrencyOptions,
  CURRENCY_INFO,
  type SupportedCurrency,
  type CurrencyFormatOptions,
} from './currency';

// Re-export convenience currency formatters
export {
  formatNGN,
  formatZAR,
  formatCNY,
  formatINR,
  formatKRW,
  formatBRL,
  formatMXN,
} from './convenience';

// Percentage formatting
export function formatPercentage(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

// Phone number formatting
export function formatPhoneNumber(phone: string): string {
  // Remove all non-digits
  const cleaned = phone.replace(/\D/g, '');

  // Check for US/Canada format
  if (cleaned.length === 11 && cleaned[0] === '1') {
    const area = cleaned.slice(1, 4);
    const exchange = cleaned.slice(4, 7);
    const number = cleaned.slice(7, 11);
    return `+1 (${area}) ${exchange}-${number}`;
  } else if (cleaned.length === 10) {
    const area = cleaned.slice(0, 3);
    const exchange = cleaned.slice(3, 6);
    const number = cleaned.slice(6, 10);
    return `(${area}) ${exchange}-${number}`;
  }

  return phone; // Return original if we can't format
}

// Date formatting utilities
export function formatDate(
  date: Date | string | number,
  options?: Intl.DateTimeFormatOptions
): string {
  const dateObj = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date;

  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  };

  return dateObj.toLocaleDateString('en-US', { ...defaultOptions, ...options });
}

export function formatDateTime(date: Date | string | number): string {
  return formatDate(date, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

export function formatRelativeTime(date: Date | string | number): string {
  const now = new Date();
  const dateObj = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date;
  const diffInSeconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000);

  if (diffInSeconds < 60) return 'just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
  if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)} days ago`;

  return formatDate(dateObj);
}

// String utilities
export function truncate(text: string, length = 100, suffix = '...'): string {
  if (text.length <= length) return text;
  return text.slice(0, length - suffix.length) + suffix;
}

export function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
}

export function titleCase(text: string): string {
  return text
    .split(' ')
    .map((word) => capitalize(word))
    .join(' ');
}

export function kebabCase(text: string): string {
  return text
    .replace(/([a-z])([A-Z])/g, '$1-$2')
    .replace(/[\s_]+/g, '-')
    .toLowerCase();
}

export function camelCase(text: string): string {
  return text
    .replace(/[-_\s]+(.)?/g, (_, char) => (char ? char.toUpperCase() : ''))
    .replace(/^(.)/, (_, char) => char.toLowerCase());
}

// ID generation utilities
export function generateId(prefix?: string): string {
  const timestamp = Date.now().toString(36);
  const randomPart = Math.random().toString(36).substring(2, 8);
  const id = `${timestamp}${randomPart}`;
  return prefix ? `${prefix}_${id}` : id;
}

export function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c == 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

// Network/Technical formatting
export function formatMACAddress(mac: string): string {
  // Remove all non-alphanumeric characters
  const cleaned = mac.replace(/[^a-fA-F0-9]/g, '');

  // Add colons every two characters
  if (cleaned.length === 12) {
    return cleaned.match(/.{2}/g)?.join(':').toUpperCase() || mac;
  }

  return mac;
}

export function formatIPAddress(ip: string): string {
  // Basic IPv4 validation and formatting
  const parts = ip.split('.');
  if (
    parts.length === 4 &&
    parts.every((part) => {
      const num = parseInt(part);
      return !isNaN(num) && num >= 0 && num <= 255;
    })
  ) {
    return parts.map((part) => parseInt(part).toString()).join('.');
  }

  return ip;
}

// ISP-specific formatting
export function formatBandwidth(mbps: number): string {
  if (mbps >= 1000) {
    return `${(mbps / 1000).toFixed(1)} Gbps`;
  }
  return `${mbps} Mbps`;
}

export function formatUsage(bytes: number, total?: number): string {
  const formatted = formatFileSize(bytes);
  if (total) {
    const percentage = formatPercentage(bytes / total);
    return `${formatted} of ${formatFileSize(total)} (${percentage})`;
  }
  return formatted;
}
