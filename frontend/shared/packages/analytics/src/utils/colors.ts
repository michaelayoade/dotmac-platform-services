import type { BusinessIntelligenceInsight, KPIMetric } from '../types';

// Default color palettes
export const DEFAULT_CHART_COLORS = [
  '#3B82F6', // Blue
  '#EF4444', // Red
  '#10B981', // Green
  '#F59E0B', // Yellow
  '#8B5CF6', // Purple
  '#F97316', // Orange
  '#06B6D4', // Cyan
  '#84CC16', // Lime
  '#EC4899', // Pink
  '#6B7280', // Gray
];

export const SEVERITY_COLORS = {
  low: {
    bg: 'bg-blue-100',
    text: 'text-blue-800',
    border: 'border-blue-200',
    hex: '#3B82F6',
  },
  medium: {
    bg: 'bg-yellow-100',
    text: 'text-yellow-800',
    border: 'border-yellow-200',
    hex: '#F59E0B',
  },
  high: {
    bg: 'bg-orange-100',
    text: 'text-orange-800',
    border: 'border-orange-200',
    hex: '#F97316',
  },
  critical: {
    bg: 'bg-red-100',
    text: 'text-red-800',
    border: 'border-red-200',
    hex: '#EF4444',
  },
};

export const STATUS_COLORS = {
  good: {
    bg: 'bg-green-100',
    text: 'text-green-800',
    border: 'border-green-200',
    hex: '#10B981',
    dot: 'bg-green-500',
  },
  warning: {
    bg: 'bg-yellow-100',
    text: 'text-yellow-800',
    border: 'border-yellow-200',
    hex: '#F59E0B',
    dot: 'bg-yellow-500',
  },
  critical: {
    bg: 'bg-red-100',
    text: 'text-red-800',
    border: 'border-red-200',
    hex: '#EF4444',
    dot: 'bg-red-500',
  },
  unknown: {
    bg: 'bg-gray-100',
    text: 'text-gray-800',
    border: 'border-gray-200',
    hex: '#6B7280',
    dot: 'bg-gray-400',
  },
};

export const TREND_COLORS = {
  up: {
    text: 'text-green-600',
    hex: '#10B981',
  },
  down: {
    text: 'text-red-600',
    hex: '#EF4444',
  },
  stable: {
    text: 'text-gray-600',
    hex: '#6B7280',
  },
};

export const generateColors = (
  count: number,
  palette: string[] = DEFAULT_CHART_COLORS
): string[] => {
  if (count <= palette.length) {
    return palette.slice(0, count);
  }

  const colors: string[] = [...palette];

  // Generate additional colors by varying saturation and lightness
  for (let i = palette.length; i < count; i++) {
    const baseColor = palette[i % palette.length];
    const variation = Math.floor(i / palette.length);

    // Convert hex to HSL and adjust
    const hsl = hexToHsl(baseColor);
    if (hsl) {
      hsl.s = Math.max(0.3, hsl.s - variation * 0.1); // Reduce saturation
      hsl.l = Math.min(0.8, hsl.l + variation * 0.05); // Increase lightness
      colors.push(hslToHex(hsl.h, hsl.s, hsl.l));
    } else {
      // Fallback to cycling through base colors
      colors.push(palette[i % palette.length]);
    }
  }

  return colors;
};

export const getStatusColor = (
  status: KPIMetric['status'],
  format: 'hex' | 'classes' | 'dot' = 'classes'
) => {
  const colorConfig = STATUS_COLORS[status];

  switch (format) {
    case 'hex':
      return colorConfig.hex;
    case 'dot':
      return colorConfig.dot;
    case 'classes':
    default:
      return {
        background: colorConfig.bg,
        text: colorConfig.text,
        border: colorConfig.border,
      };
  }
};

export const getSeverityColor = (
  severity: BusinessIntelligenceInsight['severity'],
  format: 'hex' | 'classes' = 'classes'
) => {
  const colorConfig = SEVERITY_COLORS[severity];

  switch (format) {
    case 'hex':
      return colorConfig.hex;
    case 'classes':
    default:
      return {
        background: colorConfig.bg,
        text: colorConfig.text,
        border: colorConfig.border,
      };
  }
};

export const getTrendColor = (
  trend: 'up' | 'down' | 'stable',
  format: 'hex' | 'classes' = 'classes'
) => {
  const colorConfig = TREND_COLORS[trend];

  switch (format) {
    case 'hex':
      return colorConfig.hex;
    case 'classes':
    default:
      return colorConfig.text;
  }
};

// Color utility functions
export const hexToRgb = (hex: string): { r: number; g: number; b: number } | null => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
};

export const rgbToHex = (r: number, g: number, b: number): string => {
  return '#' + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
};

export const hexToHsl = (hex: string): { h: number; s: number; l: number } | null => {
  const rgb = hexToRgb(hex);
  if (!rgb) return null;

  const r = rgb.r / 255;
  const g = rgb.g / 255;
  const b = rgb.b / 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

  if (max === min) {
    h = s = 0; // achromatic
  } else {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);

    switch (max) {
      case r:
        h = (g - b) / d + (g < b ? 6 : 0);
        break;
      case g:
        h = (b - r) / d + 2;
        break;
      case b:
        h = (r - g) / d + 4;
        break;
    }
    h /= 6;
  }

  return { h, s, l };
};

export const hslToHex = (h: number, s: number, l: number): string => {
  const hue2rgb = (p: number, q: number, t: number): number => {
    if (t < 0) t += 1;
    if (t > 1) t -= 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
    return p;
  };

  let r: number, g: number, b: number;

  if (s === 0) {
    r = g = b = l; // achromatic
  } else {
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    r = hue2rgb(p, q, h + 1 / 3);
    g = hue2rgb(p, q, h);
    b = hue2rgb(p, q, h - 1 / 3);
  }

  return rgbToHex(Math.round(r * 255), Math.round(g * 255), Math.round(b * 255));
};

export const adjustBrightness = (hex: string, percent: number): string => {
  const rgb = hexToRgb(hex);
  if (!rgb) return hex;

  const adjust = (value: number) => {
    const adjusted = value + (value * percent) / 100;
    return Math.max(0, Math.min(255, Math.round(adjusted)));
  };

  return rgbToHex(adjust(rgb.r), adjust(rgb.g), adjust(rgb.b));
};

export const adjustSaturation = (hex: string, percent: number): string => {
  const hsl = hexToHsl(hex);
  if (!hsl) return hex;

  hsl.s = Math.max(0, Math.min(1, hsl.s + percent / 100));
  return hslToHex(hsl.h, hsl.s, hsl.l);
};

export const getContrastColor = (hex: string): string => {
  const rgb = hexToRgb(hex);
  if (!rgb) return '#000000';

  // Calculate luminance
  const luminance = (0.299 * rgb.r + 0.587 * rgb.g + 0.114 * rgb.b) / 255;

  return luminance > 0.5 ? '#000000' : '#FFFFFF';
};

export const generateGradient = (startColor: string, endColor: string, steps: number): string[] => {
  const startRgb = hexToRgb(startColor);
  const endRgb = hexToRgb(endColor);

  if (!startRgb || !endRgb) return [startColor, endColor];

  const gradient: string[] = [];

  for (let i = 0; i < steps; i++) {
    const ratio = i / (steps - 1);
    const r = Math.round(startRgb.r + ratio * (endRgb.r - startRgb.r));
    const g = Math.round(startRgb.g + ratio * (endRgb.g - startRgb.g));
    const b = Math.round(startRgb.b + ratio * (endRgb.b - startRgb.b));

    gradient.push(rgbToHex(r, g, b));
  }

  return gradient;
};
