/**
 * Focus Styles Utility
 *
 * Standardized focus ring styles for consistent accessibility across components.
 * Use these classes to ensure all interactive elements have consistent focus states.
 */

/**
 * Default focus ring style for most interactive elements.
 * Uses focus-visible to only show focus ring on keyboard navigation.
 * Uses ring-accent for consistent branding across all portals.
 */
export const focusRing =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-surface";

/**
 * Focus ring without offset - for elements with borders or backgrounds
 * where offset would create visual gaps. Uses ring-inset for nav items.
 */
export const focusRingInset =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-inset";

/**
 * Focus ring within - for use with focus-within containers.
 */
export const focusWithinRing =
  "focus-within:outline-none focus-within:ring-2 focus-within:ring-accent focus-within:ring-offset-2 focus-within:ring-offset-surface";

/**
 * Subtle focus style - for elements that need less prominent focus indication.
 */
export const focusRingSubtle =
  "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent/50 focus-visible:ring-offset-1 focus-visible:ring-offset-surface";

/**
 * Focus styles for destructive actions.
 */
export const focusRingDestructive =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-status-error focus-visible:ring-offset-2";

/**
 * Focus styles object for convenience.
 */
export const focusStyles = {
  ring: focusRing,
  ringInset: focusRingInset,
  ringWithin: focusWithinRing,
  ringSubtle: focusRingSubtle,
  ringDestructive: focusRingDestructive,
} as const;

export default focusStyles;
