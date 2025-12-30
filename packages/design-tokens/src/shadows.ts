/**
 * @dotmac/design-tokens - Shadow System
 *
 * Box shadows and elevation tokens
 */

// ============================================================================
// Box Shadows
// ============================================================================

export const shadows = {
  none: "none",
  xs: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
  sm: "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
  DEFAULT: "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
  md: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
  lg: "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
  xl: "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
  "2xl": "0 25px 50px -12px rgb(0 0 0 / 0.25)",
  inner: "inset 0 2px 4px 0 rgb(0 0 0 / 0.05)",
} as const;

// ============================================================================
// Elevation Levels (Material Design inspired)
// ============================================================================

export const elevation = {
  0: shadows.none,
  1: shadows.xs,
  2: shadows.sm,
  4: shadows.md,
  8: shadows.lg,
  16: shadows.xl,
  24: shadows["2xl"],
} as const;

// ============================================================================
// Focus Ring Shadows
// ============================================================================

export const focusRing = {
  // Primary blue focus ring
  primary: "0 0 0 2px #ffffff, 0 0 0 4px #3b82f6",
  // Error focus ring
  error: "0 0 0 2px #ffffff, 0 0 0 4px #ef4444",
  // Success focus ring
  success: "0 0 0 2px #ffffff, 0 0 0 4px #22c55e",
  // Neutral focus ring
  neutral: "0 0 0 2px #ffffff, 0 0 0 4px #64748b",
  // Inset focus ring
  inset: "inset 0 0 0 2px #3b82f6",
} as const;

// ============================================================================
// Glow Effects
// ============================================================================

export const glow = {
  primary: "0 0 20px rgb(59 130 246 / 0.5)",
  success: "0 0 20px rgb(34 197 94 / 0.5)",
  warning: "0 0 20px rgb(249 115 22 / 0.5)",
  error: "0 0 20px rgb(239 68 68 / 0.5)",
  purple: "0 0 20px rgb(168 85 247 / 0.5)",
} as const;

// ============================================================================
// Component-specific Shadows
// ============================================================================

export const componentShadows = {
  // Cards
  card: shadows.sm,
  cardHover: shadows.md,
  cardElevated: shadows.lg,

  // Buttons
  button: shadows.xs,
  buttonHover: shadows.sm,
  buttonActive: "inset 0 1px 2px 0 rgb(0 0 0 / 0.1)",

  // Inputs
  input: shadows.xs,
  inputFocus: focusRing.primary,

  // Modals & Dialogs
  modal: shadows["2xl"],
  dialog: shadows.xl,
  sheet: shadows.xl,

  // Dropdowns & Popovers
  dropdown: shadows.lg,
  popover: shadows.lg,
  tooltip: shadows.md,

  // Navigation
  navbar: shadows.sm,
  sidebar: shadows.lg,
  header: "0 1px 3px 0 rgb(0 0 0 / 0.1)",

  // Toast & Notifications
  toast: shadows.xl,
  notification: shadows.lg,
} as const;
