/**
 * @dotmac/design-tokens - Color System
 *
 * Unified color tokens supporting:
 * - Portal-specific palettes (admin, tenant, reseller, technician, management)
 * - Semantic colors (success, warning, error, info)
 * - Status colors (online, offline, degraded)
 * - ISP-specific brand colors
 *
 * ## WCAG Contrast Guidelines
 *
 * All color combinations should meet WCAG 2.1 AA standards:
 * - Normal text: minimum 4.5:1 contrast ratio
 * - Large text (18pt+ or 14pt bold): minimum 3:1 contrast ratio
 * - UI components & graphics: minimum 3:1 contrast ratio
 *
 * ## Semantic Color Mapping
 *
 * | Semantic   | Token       | Tailwind   | Use Case                    |
 * |------------|-------------|------------|-----------------------------|
 * | Success    | network     | green-*    | Positive states, connected  |
 * | Warning    | alert       | orange-*   | Caution, pending actions    |
 * | Error      | critical    | red-*      | Errors, destructive actions |
 * | Info       | primary     | blue-*     | Informational, neutral      |
 * | Neutral    | secondary   | slate-*    | Backgrounds, borders        |
 * | Premium    | purple      | purple-*   | Reseller, premium features  |
 *
 * ## Dark Mode Contrast
 *
 * Text on dark surfaces (surface: ~17% lightness):
 * - text-primary:   98% lightness → ~15:1 contrast ✓ AAA
 * - text-secondary: 75% lightness → ~8:1 contrast  ✓ AAA
 * - text-muted:     55% lightness → ~4.5:1 contrast ✓ AA
 *
 * Text on light surfaces (surface: 100% lightness):
 * - text-primary:   17% lightness → ~12:1 contrast ✓ AAA
 * - text-secondary: 37% lightness → ~7:1 contrast  ✓ AAA
 * - text-muted:     52% lightness → ~4.5:1 contrast ✓ AA
 *
 * ## Border Colors
 *
 * Borders use a subtle accent tint (hue ~152-158°) for brand cohesion:
 * - Light mode: 152° hue, 6-12% saturation, 72-88% lightness
 * - Dark mode:  158° hue, 8-18% saturation, 24-38% lightness
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
  | "tenant"
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
  background: { light: string; dark: string };
  surface: { light: string; dark: string };
  text: { light: string; dark: string };
  sidebarMode: "dark" | "light" | "none";
}

export const portalColors: Record<PortalVariant, PortalColorScheme> = {
  admin: {
    name: "Admin Portal",
    primary: colors.primary,
    accent: colors.network[500],
    background: { light: "#f8fafc", dark: "#0f172a" },
    surface: { light: "#ffffff", dark: "#1e293b" },
    text: { light: "#1e293b", dark: "#f1f5f9" },
    sidebarMode: "dark",
  },
  tenant: {
    name: "Tenant Portal",
    primary: colors.network,
    accent: colors.primary[500],
    background: { light: "#f0f9ff", dark: "#0c1929" },
    surface: { light: "#ffffff", dark: "#1e293b" },
    text: { light: "#1e40af", dark: "#93c5fd" },
    sidebarMode: "none",
  },
  reseller: {
    name: "Reseller Portal",
    primary: colors.purple,
    accent: colors.network[500],
    background: { light: "#fdf4ff", dark: "#1a0a29" },
    surface: { light: "#ffffff", dark: "#2d1a47" },
    text: { light: "#581c87", dark: "#e9d5ff" },
    sidebarMode: "light",
  },
  technician: {
    name: "Technician Portal",
    primary: colors.network,
    accent: colors.alert[500],
    background: { light: "#f0fdf4", dark: "#0a1f14" },
    surface: { light: "#ffffff", dark: "#14332a" },
    text: { light: "#14532d", dark: "#bbf7d0" },
    sidebarMode: "light",
  },
  management: {
    name: "Management Console",
    primary: colors.alert,
    accent: colors.primary[500],
    background: { light: "#f9fafb", dark: "#111827" },
    surface: { light: "#ffffff", dark: "#1f2937" },
    text: { light: "#111827", dark: "#f3f4f6" },
    sidebarMode: "dark",
  },
  platformAdmin: {
    name: "Platform Admin",
    primary: colors.primary,
    accent: colors.cyan[500],
    background: { light: "#f8fafc", dark: "#0f172a" },
    surface: { light: "#ffffff", dark: "#1e293b" },
    text: { light: "#1e293b", dark: "#f1f5f9" },
    sidebarMode: "dark",
  },
  platformReseller: {
    name: "Platform Reseller",
    primary: colors.alert,
    accent: colors.network[500],
    background: { light: "#fff7ed", dark: "#1c1007" },
    surface: { light: "#ffffff", dark: "#2d1f0f" },
    text: { light: "#7c2d12", dark: "#fed7aa" },
    sidebarMode: "light",
  },
  platformTenant: {
    name: "Platform Tenant",
    primary: colors.purple,
    accent: colors.primary[500],
    background: { light: "#faf5ff", dark: "#1a0a29" },
    surface: { light: "#ffffff", dark: "#2d1a47" },
    text: { light: "#581c87", dark: "#e9d5ff" },
    sidebarMode: "light",
  },
  insights: {
    name: "Dotmac Insights",
    primary: colors.dotmac,
    accent: colors.alert[400],
    background: { light: "#f0fdfa", dark: "#0b1220" },
    surface: { light: "#ffffff", dark: "#0f172a" },
    text: { light: "#134e4a", dark: "#e2e8f0" },
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

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const normalized = hex.startsWith("#") ? hex.slice(1) : hex;
  const value = normalized.length === 3
    ? normalized.split("").map((c) => c + c).join("")
    : normalized;
  const r = parseInt(value.slice(0, 2), 16);
  const g = parseInt(value.slice(2, 4), 16);
  const b = parseInt(value.slice(4, 6), 16);
  return { r, g, b };
}

function rgbToHex(r: number, g: number, b: number): string {
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

function srgbToLinear(channel: number): number {
  const c = channel / 255;
  return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}

function linearToSrgb(channel: number): number {
  const c = channel <= 0.0031308
    ? 12.92 * channel
    : 1.055 * Math.pow(channel, 1 / 2.4) - 0.055;
  return Math.round(clamp(c, 0, 1) * 255);
}

function rgbToOklab(r: number, g: number, b: number): { L: number; a: number; b: number } {
  const lr = srgbToLinear(r);
  const lg = srgbToLinear(g);
  const lb = srgbToLinear(b);

  const l = 0.4122214708 * lr + 0.5363325363 * lg + 0.0514459929 * lb;
  const m = 0.2119034982 * lr + 0.6806995451 * lg + 0.1073969566 * lb;
  const s = 0.0883024619 * lr + 0.2817188376 * lg + 0.6299787005 * lb;

  const lRoot = Math.cbrt(l);
  const mRoot = Math.cbrt(m);
  const sRoot = Math.cbrt(s);

  return {
    L: 0.2104542553 * lRoot + 0.7936177850 * mRoot - 0.0040720468 * sRoot,
    a: 1.9779984951 * lRoot - 2.4285922050 * mRoot + 0.4505937099 * sRoot,
    b: 0.0259040371 * lRoot + 0.7827717662 * mRoot - 0.8086757660 * sRoot,
  };
}

function oklabToRgb(L: number, a: number, b: number): { r: number; g: number; b: number } {
  const l = L + 0.3963377774 * a + 0.2158037573 * b;
  const m = L - 0.1055613458 * a - 0.0638541728 * b;
  const s = L - 0.0894841775 * a - 1.2914855480 * b;

  const l3 = l ** 3;
  const m3 = m ** 3;
  const s3 = s ** 3;

  const rLinear = 4.0767416621 * l3 - 3.3077115913 * m3 + 0.2309699292 * s3;
  const gLinear = -1.2684380046 * l3 + 2.6097574011 * m3 - 0.3413193965 * s3;
  const bLinear = -0.0041960863 * l3 - 0.7034186147 * m3 + 1.7076147010 * s3;

  return {
    r: linearToSrgb(rLinear),
    g: linearToSrgb(gLinear),
    b: linearToSrgb(bLinear),
  };
}

function oklabToOklch(L: number, a: number, b: number): { L: number; C: number; h: number } {
  const C = Math.sqrt(a * a + b * b);
  const h = Math.atan2(b, a);
  return { L, C, h };
}

function oklchToOklab(L: number, C: number, h: number): { L: number; a: number; b: number } {
  return {
    L,
    a: C * Math.cos(h),
    b: C * Math.sin(h),
  };
}

function oklchToHex(L: number, C: number, h: number): string {
  const lab = oklchToOklab(L, C, h);
  const rgb = oklabToRgb(lab.L, lab.a, lab.b);
  return rgbToHex(rgb.r, rgb.g, rgb.b);
}

/**
 * Generate a complete color scale from a single base color
 */
export function generateColorScale(baseColor: string): ColorScale {
  const { r, g, b } = hexToRgb(baseColor);
  const lab = rgbToOklab(r, g, b);
  const oklch = oklabToOklch(lab.L, lab.a, lab.b);

  const lightnessScale: Record<keyof ColorScale, number> = {
    50: 0.97,
    100: 0.93,
    200: 0.88,
    300: 0.80,
    400: 0.72,
    500: 0.66,
    600: 0.58,
    700: 0.50,
    800: 0.42,
    900: 0.34,
    950: 0.24,
  };

  const baseTarget = lightnessScale[500];
  const delta = oklch.L - baseTarget;

  const adjustChroma = (L: number) => {
    const distance = Math.abs(L - oklch.L);
    const dampen = 1 - Math.min(0.35, distance * 1.1);
    return Math.max(0, oklch.C * dampen);
  };

  const scaleKeys: Array<keyof ColorScale> = [
    50,
    100,
    200,
    300,
    400,
    500,
    600,
    700,
    800,
    900,
    950,
  ];

  const scale = scaleKeys.reduce(
    (scale, shade) => {
      const L = clamp(lightnessScale[shade] + delta, 0.02, 0.98);
      const C = adjustChroma(L);
      scale[shade] = oklchToHex(L, C, oklch.h);
      return scale;
    },
    {} as ColorScale
  );
  scale[500] = baseColor;
  return scale;
}

/**
 * Get portal color scheme by variant
 */
export function getPortalColors(variant: PortalVariant): PortalColorScheme {
  return portalColors[variant];
}
