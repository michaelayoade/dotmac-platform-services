/**
 * @dotmac/design-tokens - Typography System
 *
 * Font families, sizes, weights, and line heights
 */

// ============================================================================
// Font Families
// ============================================================================

export const fontFamily = {
  sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
  serif: ["Georgia", "Cambria", "serif"],
  mono: ["JetBrains Mono", "Fira Code", "monospace"],
} as const;

// ============================================================================
// Font Sizes with Line Height & Letter Spacing
// ============================================================================

export interface FontSizeConfig {
  size: string;
  lineHeight: string;
  letterSpacing: string;
}

export const fontSize: Record<string, FontSizeConfig> = {
  xs: { size: "0.75rem", lineHeight: "1rem", letterSpacing: "0.05em" },
  sm: { size: "0.875rem", lineHeight: "1.25rem", letterSpacing: "0.025em" },
  base: { size: "1rem", lineHeight: "1.5rem", letterSpacing: "0em" },
  lg: { size: "1.125rem", lineHeight: "1.75rem", letterSpacing: "-0.025em" },
  xl: { size: "1.25rem", lineHeight: "1.75rem", letterSpacing: "-0.025em" },
  "2xl": { size: "1.5rem", lineHeight: "2rem", letterSpacing: "-0.05em" },
  "3xl": { size: "1.875rem", lineHeight: "2.25rem", letterSpacing: "-0.05em" },
  "4xl": { size: "2.25rem", lineHeight: "2.5rem", letterSpacing: "-0.05em" },
  "5xl": { size: "3rem", lineHeight: "1.2", letterSpacing: "-0.05em" },
  "6xl": { size: "3.75rem", lineHeight: "1.1", letterSpacing: "-0.05em" },
} as const;

// ============================================================================
// Font Weights
// ============================================================================

export const fontWeight = {
  thin: "100",
  extralight: "200",
  light: "300",
  normal: "400",
  medium: "500",
  semibold: "600",
  bold: "700",
  extrabold: "800",
  black: "900",
} as const;

// ============================================================================
// Portal-specific Typography
// ============================================================================

export type PortalTypographyVariant =
  | "admin"
  | "customer"
  | "reseller"
  | "technician"
  | "management";

export interface PortalTypography {
  headingSize: keyof typeof fontSize;
  bodySize: keyof typeof fontSize;
  density: "compact" | "comfortable" | "spacious";
}

export const portalTypography: Record<PortalTypographyVariant, PortalTypography> = {
  admin: {
    headingSize: "2xl",
    bodySize: "sm",
    density: "comfortable",
  },
  customer: {
    headingSize: "3xl",
    bodySize: "base",
    density: "spacious",
  },
  reseller: {
    headingSize: "2xl",
    bodySize: "sm",
    density: "comfortable",
  },
  technician: {
    headingSize: "xl",
    bodySize: "sm",
    density: "compact",
  },
  management: {
    headingSize: "2xl",
    bodySize: "sm",
    density: "comfortable",
  },
} as const;

// ============================================================================
// Text Styles (Presets)
// ============================================================================

export const textStyles = {
  // Headings
  h1: {
    fontSize: fontSize["4xl"].size,
    lineHeight: fontSize["4xl"].lineHeight,
    fontWeight: fontWeight.bold,
    letterSpacing: fontSize["4xl"].letterSpacing,
  },
  h2: {
    fontSize: fontSize["3xl"].size,
    lineHeight: fontSize["3xl"].lineHeight,
    fontWeight: fontWeight.bold,
    letterSpacing: fontSize["3xl"].letterSpacing,
  },
  h3: {
    fontSize: fontSize["2xl"].size,
    lineHeight: fontSize["2xl"].lineHeight,
    fontWeight: fontWeight.semibold,
    letterSpacing: fontSize["2xl"].letterSpacing,
  },
  h4: {
    fontSize: fontSize.xl.size,
    lineHeight: fontSize.xl.lineHeight,
    fontWeight: fontWeight.semibold,
    letterSpacing: fontSize.xl.letterSpacing,
  },
  h5: {
    fontSize: fontSize.lg.size,
    lineHeight: fontSize.lg.lineHeight,
    fontWeight: fontWeight.medium,
    letterSpacing: fontSize.lg.letterSpacing,
  },
  h6: {
    fontSize: fontSize.base.size,
    lineHeight: fontSize.base.lineHeight,
    fontWeight: fontWeight.medium,
    letterSpacing: fontSize.base.letterSpacing,
  },

  // Body text
  bodyLarge: {
    fontSize: fontSize.lg.size,
    lineHeight: fontSize.lg.lineHeight,
    fontWeight: fontWeight.normal,
    letterSpacing: fontSize.lg.letterSpacing,
  },
  body: {
    fontSize: fontSize.base.size,
    lineHeight: fontSize.base.lineHeight,
    fontWeight: fontWeight.normal,
    letterSpacing: fontSize.base.letterSpacing,
  },
  bodySmall: {
    fontSize: fontSize.sm.size,
    lineHeight: fontSize.sm.lineHeight,
    fontWeight: fontWeight.normal,
    letterSpacing: fontSize.sm.letterSpacing,
  },

  // Labels
  label: {
    fontSize: fontSize.sm.size,
    lineHeight: fontSize.sm.lineHeight,
    fontWeight: fontWeight.medium,
    letterSpacing: fontSize.sm.letterSpacing,
  },
  labelSmall: {
    fontSize: fontSize.xs.size,
    lineHeight: fontSize.xs.lineHeight,
    fontWeight: fontWeight.medium,
    letterSpacing: fontSize.xs.letterSpacing,
  },

  // Captions
  caption: {
    fontSize: fontSize.xs.size,
    lineHeight: fontSize.xs.lineHeight,
    fontWeight: fontWeight.normal,
    letterSpacing: fontSize.xs.letterSpacing,
  },

  // Code
  code: {
    fontFamily: fontFamily.mono.join(", "),
    fontSize: fontSize.sm.size,
    lineHeight: fontSize.sm.lineHeight,
    fontWeight: fontWeight.normal,
  },
} as const;
