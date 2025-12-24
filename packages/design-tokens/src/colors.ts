/**
 * @dotmac/design-tokens - Color System
 *
 * Unified color tokens supporting:
 * - Portal-specific palettes (admin, customer, reseller, technician, management)
 * - Semantic colors (success, warning, error, info)
 * - Status colors (online, offline, degraded)
 * - ISP-specific brand colors
 */

// ============================================================================
// Color Palette Type
// ============================================================================

export interface ColorScale {
  50: string;
  100: string;
  200: string;
  300: string;
  400: string;
  500: string;
  600: string;
  700: string;
  800: string;
  900: string;
  950: string;
}

// ============================================================================
// Core Color Palettes
// ============================================================================

export const colors = {
  // Primary Blue - Main brand color
  primary: {
    50: "#eff6ff",
    100: "#dbeafe",
    200: "#bfdbfe",
    300: "#93c5fd",
    400: "#60a5fa",
    500: "#3b82f6",
    600: "#2563eb",
    700: "#1d4ed8",
    800: "#1e40af",
    900: "#1e3a8a",
    950: "#172554",
  },

  // Secondary Slate - Neutral tones
  secondary: {
    50: "#f8fafc",
    100: "#f1f5f9",
    200: "#e2e8f0",
    300: "#cbd5e1",
    400: "#94a3b8",
    500: "#64748b",
    600: "#475569",
    700: "#334155",
    800: "#1e293b",
    900: "#0f172a",
    950: "#020617",
  },

  // Neutral Gray
  neutral: {
    50: "#fafafa",
    100: "#f5f5f5",
    200: "#e5e5e5",
    300: "#d4d4d4",
    400: "#a3a3a3",
    500: "#737373",
    600: "#525252",
    700: "#404040",
    800: "#262626",
    900: "#171717",
    950: "#0a0a0a",
  },

  // Network Green - Connection, active states
  network: {
    50: "#f0fdf4",
    100: "#dcfce7",
    200: "#bbf7d0",
    300: "#86efac",
    400: "#4ade80",
    500: "#22c55e",
    600: "#16a34a",
    700: "#15803d",
    800: "#166534",
    900: "#14532d",
    950: "#052e16",
  },

  // Alert Orange - Warnings
  alert: {
    50: "#fff7ed",
    100: "#ffedd5",
    200: "#fed7aa",
    300: "#fdba74",
    400: "#fb923c",
    500: "#f97316",
    600: "#ea580c",
    700: "#c2410c",
    800: "#9a3412",
    900: "#7c2d12",
    950: "#431407",
  },

  // Critical Red - Errors
  critical: {
    50: "#fef2f2",
    100: "#fee2e2",
    200: "#fecaca",
    300: "#fca5a5",
    400: "#f87171",
    500: "#ef4444",
    600: "#dc2626",
    700: "#b91c1c",
    800: "#991b1b",
    900: "#7f1d1d",
    950: "#450a0a",
  },

  // Purple - Premium, reseller
  purple: {
    50: "#faf5ff",
    100: "#f3e8ff",
    200: "#e9d5ff",
    300: "#d8b4fe",
    400: "#c084fc",
    500: "#a855f7",
    600: "#9333ea",
    700: "#7c3aed",
    800: "#6b21a8",
    900: "#581c87",
    950: "#3b0764",
  },

  // Cyan - Technical, monitoring
  cyan: {
    50: "#ecfeff",
    100: "#cffafe",
    200: "#a5f3fc",
    300: "#67e8f9",
    400: "#22d3ee",
    500: "#06b6d4",
    600: "#0891b2",
    700: "#0e7490",
    800: "#155e75",
    900: "#164e63",
    950: "#083344",
  },

  // Dotmac Teal - Insights UI primary
  dotmac: {
    50: "#e6fffa",
    100: "#b8fff0",
    200: "#7affe1",
    300: "#3af7d2",
    400: "#12e8c2",
    500: "#00d4aa",
    600: "#00b38f",
    700: "#008f74",
    800: "#006f5c",
    900: "#004c3f",
    950: "#003428",
  },
} as const;

// ============================================================================
// Semantic Colors
// ============================================================================

export const semanticColors = {
  success: colors.network[500],
  successLight: colors.network[100],
  successDark: colors.network[700],

  warning: colors.alert[500],
  warningLight: colors.alert[100],
  warningDark: colors.alert[700],

  error: colors.critical[500],
  errorLight: colors.critical[100],
  errorDark: colors.critical[700],

  info: colors.primary[500],
  infoLight: colors.primary[100],
  infoDark: colors.primary[700],
} as const;

// ============================================================================
// Status Colors (Network/Service)
// ============================================================================

export const statusColors = {
  online: colors.network[500],
  offline: colors.critical[500],
  degraded: colors.alert[500],
  maintenance: colors.purple[500],
  unknown: colors.neutral[400],
} as const;

// ============================================================================
// Portal Color Schemes
// ============================================================================

export type PortalVariant =
  | "admin"
  | "customer"
  | "reseller"
  | "technician"
  | "management"
  | "platformAdmin"
  | "platformReseller"
  | "platformTenant"
  | "insights";

export interface PortalColorScheme {
  name: string;
  primary: ColorScale;
  accent: string;
  background: string;
  surface: string;
  text: string;
  sidebarMode: "dark" | "light" | "none";
}

export const portalColors: Record<PortalVariant, PortalColorScheme> = {
  admin: {
    name: "Admin Portal",
    primary: colors.primary,
    accent: colors.network[500],
    background: "#f8fafc",
    surface: "#ffffff",
    text: "#1e293b",
    sidebarMode: "dark",
  },
  customer: {
    name: "Customer Portal",
    primary: colors.network,
    accent: colors.primary[500],
    background: "#f0f9ff",
    surface: "#ffffff",
    text: "#1e40af",
    sidebarMode: "none",
  },
  reseller: {
    name: "Reseller Portal",
    primary: colors.purple,
    accent: colors.network[500],
    background: "#fdf4ff",
    surface: "#ffffff",
    text: "#7c2d12",
    sidebarMode: "light",
  },
  technician: {
    name: "Technician Portal",
    primary: colors.network,
    accent: colors.alert[500],
    background: "#f0fdf4",
    surface: "#ffffff",
    text: "#14532d",
    sidebarMode: "light",
  },
  management: {
    name: "Management Console",
    primary: colors.alert,
    accent: colors.primary[500],
    background: "#f9fafb",
    surface: "#ffffff",
    text: "#111827",
    sidebarMode: "dark",
  },
  platformAdmin: {
    name: "Platform Admin",
    primary: colors.primary,
    accent: colors.cyan[500],
    background: "#f8fafc",
    surface: "#ffffff",
    text: "#1e293b",
    sidebarMode: "dark",
  },
  platformReseller: {
    name: "Platform Reseller",
    primary: colors.alert,
    accent: colors.network[500],
    background: "#fff7ed",
    surface: "#ffffff",
    text: "#7c2d12",
    sidebarMode: "light",
  },
  platformTenant: {
    name: "Platform Tenant",
    primary: colors.purple,
    accent: colors.primary[500],
    background: "#faf5ff",
    surface: "#ffffff",
    text: "#581c87",
    sidebarMode: "light",
  },
  insights: {
    name: "Dotmac Insights",
    primary: colors.dotmac,
    accent: colors.alert[400],
    background: "#0b1220",
    surface: "#0f172a",
    text: "#e2e8f0",
    sidebarMode: "dark",
  },
};

// ============================================================================
// ISP Brand Gradients
// ============================================================================

export const gradients = {
  primary: "linear-gradient(to right, #2563eb, #4f46e5, #7c3aed)",
  network: "linear-gradient(to right, #22c55e, #10b981)",
  signal: "linear-gradient(to right, #4ade80, #3b82f6, #7c3aed)",
  speed: "linear-gradient(to right, #22d3ee, #3b82f6, #7c3aed)",
  data: "linear-gradient(to right, #a855f7, #ec4899, #ef4444)",
  billing: "linear-gradient(to right, #fb923c, #f59e0b, #fbbf24)",
  premium: "linear-gradient(to right, #7c3aed, #ec4899, #ef4444)",
  enterprise: "linear-gradient(to right, #111827, #581c87, #312e81)",
} as const;

// ============================================================================
// Tailwind CSS Gradient Classes
// ============================================================================

export const gradientClasses = {
  primary: "bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600",
  network: "bg-gradient-to-r from-green-500 to-emerald-500",
  signal: "bg-gradient-to-r from-green-400 via-blue-500 to-purple-600",
  speed: "bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600",
  data: "bg-gradient-to-r from-purple-400 via-pink-500 to-red-500",
  billing: "bg-gradient-to-r from-orange-400 via-amber-500 to-yellow-500",
  premium: "bg-gradient-to-r from-purple-600 via-pink-600 to-red-600",
  enterprise: "bg-gradient-to-r from-gray-900 via-purple-900 to-indigo-900",
} as const;

// ============================================================================
// Color Utilities
// ============================================================================

/**
 * Convert hex color to HSL
 */
export function hexToHsl(hex: string): { h: number; s: number; l: number } {
  const r = parseInt(hex.slice(1, 3), 16) / 255;
  const g = parseInt(hex.slice(3, 5), 16) / 255;
  const b = parseInt(hex.slice(5, 7), 16) / 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

  if (max !== min) {
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

  return { h: h * 360, s: s * 100, l: l * 100 };
}

/**
 * Convert HSL to hex color
 */
export function hslToHex(h: number, s: number, l: number): string {
  h /= 360;
  s /= 100;
  l /= 100;

  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs(((h * 6) % 2) - 1));
  const m = l - c / 2;
  let r = 0,
    g = 0,
    b = 0;

  if (h < 1 / 6) {
    r = c;
    g = x;
  } else if (h < 2 / 6) {
    r = x;
    g = c;
  } else if (h < 3 / 6) {
    g = c;
    b = x;
  } else if (h < 4 / 6) {
    g = x;
    b = c;
  } else if (h < 5 / 6) {
    r = x;
    b = c;
  } else {
    r = c;
    b = x;
  }

  r = Math.round((r + m) * 255);
  g = Math.round((g + m) * 255);
  b = Math.round((b + m) * 255);

  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

/**
 * Generate a complete color scale from a single base color
 */
export function generateColorScale(baseColor: string): ColorScale {
  const hsl = hexToHsl(baseColor);

  return {
    50: hslToHex(hsl.h, Math.max(0, hsl.s - 20), Math.min(100, hsl.l + 45)),
    100: hslToHex(hsl.h, Math.max(0, hsl.s - 15), Math.min(100, hsl.l + 35)),
    200: hslToHex(hsl.h, Math.max(0, hsl.s - 10), Math.min(100, hsl.l + 25)),
    300: hslToHex(hsl.h, Math.max(0, hsl.s - 5), Math.min(100, hsl.l + 15)),
    400: hslToHex(hsl.h, hsl.s, Math.min(100, hsl.l + 8)),
    500: baseColor,
    600: hslToHex(hsl.h, Math.min(100, hsl.s + 5), Math.max(0, hsl.l - 8)),
    700: hslToHex(hsl.h, Math.min(100, hsl.s + 10), Math.max(0, hsl.l - 15)),
    800: hslToHex(hsl.h, Math.min(100, hsl.s + 15), Math.max(0, hsl.l - 25)),
    900: hslToHex(hsl.h, Math.min(100, hsl.s + 20), Math.max(0, hsl.l - 35)),
    950: hslToHex(hsl.h, Math.min(100, hsl.s + 25), Math.max(0, hsl.l - 45)),
  };
}

/**
 * Get portal color scheme by variant
 */
export function getPortalColors(variant: PortalVariant): PortalColorScheme {
  return portalColors[variant];
}
