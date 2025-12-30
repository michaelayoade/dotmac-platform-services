/**
 * @dotmac/design-tokens - Spacing System
 *
 * Consistent spacing, sizing, and layout tokens
 */

// ============================================================================
// Base Spacing Scale
// ============================================================================

export const spacing = {
  px: "1px",
  0: "0",
  0.5: "0.125rem", // 2px
  1: "0.25rem", // 4px
  1.5: "0.375rem", // 6px
  2: "0.5rem", // 8px
  2.5: "0.625rem", // 10px
  3: "0.75rem", // 12px
  3.5: "0.875rem", // 14px
  4: "1rem", // 16px
  5: "1.25rem", // 20px
  6: "1.5rem", // 24px
  7: "1.75rem", // 28px
  8: "2rem", // 32px
  9: "2.25rem", // 36px
  10: "2.5rem", // 40px
  11: "2.75rem", // 44px
  12: "3rem", // 48px
  14: "3.5rem", // 56px
  16: "4rem", // 64px
  20: "5rem", // 80px
  24: "6rem", // 96px
  28: "7rem", // 112px
  32: "8rem", // 128px
  36: "9rem", // 144px
  40: "10rem", // 160px
  44: "11rem", // 176px
  48: "12rem", // 192px
  52: "13rem", // 208px
  56: "14rem", // 224px
  60: "15rem", // 240px
  64: "16rem", // 256px
  72: "18rem", // 288px
  80: "20rem", // 320px
  96: "24rem", // 384px
} as const;

// ============================================================================
// Semantic Spacing
// ============================================================================

export const semanticSpacing = {
  // Component padding
  xs: spacing[1], // 4px
  sm: spacing[2], // 8px
  md: spacing[4], // 16px
  lg: spacing[6], // 24px
  xl: spacing[8], // 32px
  "2xl": spacing[12], // 48px
  "3xl": spacing[16], // 64px
  "4xl": spacing[24], // 96px

  // Gaps
  gapTight: spacing[1], // 4px
  gapNormal: spacing[2], // 8px
  gapLoose: spacing[4], // 16px
  gapWide: spacing[6], // 24px

  // Section spacing
  sectionSmall: spacing[8], // 32px
  sectionMedium: spacing[16], // 64px
  sectionLarge: spacing[24], // 96px

  // Page margins
  pageMarginMobile: spacing[4], // 16px
  pageMarginTablet: spacing[6], // 24px
  pageMarginDesktop: spacing[8], // 32px
} as const;

// ============================================================================
// Portal-specific Spacing (Density)
// ============================================================================

export type DensityLevel = "compact" | "comfortable" | "spacious";

export interface DensitySpacing {
  componentPadding: string;
  cardPadding: string;
  listItemGap: string;
  sectionGap: string;
  inputHeight: string;
  buttonHeight: string;
}

export const portalSpacing: Record<DensityLevel, DensitySpacing> = {
  compact: {
    componentPadding: spacing[2], // 8px
    cardPadding: spacing[3], // 12px
    listItemGap: spacing[1], // 4px
    sectionGap: spacing[4], // 16px
    inputHeight: spacing[8], // 32px
    buttonHeight: spacing[8], // 32px
  },
  comfortable: {
    componentPadding: spacing[3], // 12px
    cardPadding: spacing[4], // 16px
    listItemGap: spacing[2], // 8px
    sectionGap: spacing[6], // 24px
    inputHeight: spacing[10], // 40px
    buttonHeight: spacing[10], // 40px
  },
  spacious: {
    componentPadding: spacing[4], // 16px
    cardPadding: spacing[6], // 24px
    listItemGap: spacing[3], // 12px
    sectionGap: spacing[8], // 32px
    inputHeight: spacing[12], // 48px
    buttonHeight: spacing[12], // 48px
  },
} as const;

// ============================================================================
// Touch Targets (Accessibility)
// ============================================================================

export const touchTargets = {
  minimum: "44px", // WCAG minimum
  comfortable: "48px", // Recommended
  large: "56px", // Large touch targets
} as const;

// ============================================================================
// Border Radius
// ============================================================================

export const borderRadius = {
  none: "0",
  sm: "0.125rem", // 2px
  DEFAULT: "0.25rem", // 4px
  md: "0.375rem", // 6px
  lg: "0.5rem", // 8px
  xl: "0.75rem", // 12px
  "2xl": "1rem", // 16px
  "3xl": "1.5rem", // 24px
  full: "9999px",
} as const;

// ============================================================================
// Z-Index Scale
// ============================================================================

export const zIndex = {
  hide: -1,
  auto: "auto",
  base: 0,
  docked: 10,
  dropdown: 1000,
  sticky: 1100,
  banner: 1200,
  overlay: 1300,
  modal: 1400,
  popover: 1500,
  skipLink: 1600,
  toast: 1700,
  tooltip: 1800,
} as const;

// ============================================================================
// Breakpoints
// ============================================================================

export const breakpoints = {
  xs: "320px",
  sm: "640px",
  md: "768px",
  lg: "1024px",
  xl: "1280px",
  "2xl": "1536px",
} as const;

// ============================================================================
// Container Widths
// ============================================================================

export const containerWidths = {
  sm: "640px",
  md: "768px",
  lg: "1024px",
  xl: "1280px",
  "2xl": "1536px",
  full: "100%",
} as const;

// ============================================================================
// Aspect Ratios
// ============================================================================

export const aspectRatios = {
  square: "1 / 1",
  video: "16 / 9",
  photo: "4 / 3",
  portrait: "3 / 4",
  wide: "21 / 9",
} as const;
