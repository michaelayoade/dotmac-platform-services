/**
 * @dotmac/design-tokens - Motion & Animation System
 *
 * Durations, easings, and animation presets
 */

// ============================================================================
// Duration
// ============================================================================

export const duration = {
  instant: "0ms",
  fastest: "50ms",
  faster: "100ms",
  fast: "150ms",
  normal: "200ms",
  slow: "300ms",
  slower: "400ms",
  slowest: "500ms",
  lazy: "700ms",
  glacial: "1000ms",
} as const;

// ============================================================================
// Easing Functions
// ============================================================================

export const easing = {
  // Standard easings
  linear: "linear",
  ease: "ease",
  easeIn: "ease-in",
  easeOut: "ease-out",
  easeInOut: "ease-in-out",

  // Custom cubic beziers
  smooth: "cubic-bezier(0.4, 0, 0.2, 1)",
  snappy: "cubic-bezier(0.4, 0, 0, 1)",
  bouncy: "cubic-bezier(0.68, -0.55, 0.265, 1.55)",
  elastic: "cubic-bezier(0.68, -0.6, 0.32, 1.6)",

  // Spring-like
  spring: "cubic-bezier(0.175, 0.885, 0.32, 1.275)",
  springMedium: "cubic-bezier(0.34, 1.56, 0.64, 1)",
  springHard: "cubic-bezier(0.34, 2, 0.64, 1)",

  // Deceleration (entering)
  enter: "cubic-bezier(0, 0, 0.2, 1)",

  // Acceleration (exiting)
  exit: "cubic-bezier(0.4, 0, 1, 1)",
} as const;

// ============================================================================
// Animation Presets
// ============================================================================

export interface AnimationPreset {
  duration: string;
  easing: string;
}

export const animations = {
  // Micro interactions
  microFade: { duration: duration.fast, easing: easing.easeOut },
  microScale: { duration: duration.fast, easing: easing.spring },
  microSlide: { duration: duration.fast, easing: easing.snappy },

  // Component transitions
  fadeIn: { duration: duration.normal, easing: easing.easeOut },
  fadeOut: { duration: duration.fast, easing: easing.easeIn },
  slideIn: { duration: duration.normal, easing: easing.smooth },
  slideOut: { duration: duration.fast, easing: easing.smooth },
  scaleIn: { duration: duration.normal, easing: easing.spring },
  scaleOut: { duration: duration.fast, easing: easing.easeIn },

  // Modal/dialog
  modalEnter: { duration: duration.slow, easing: easing.spring },
  modalExit: { duration: duration.normal, easing: easing.easeIn },

  // Toast/notification
  toastEnter: { duration: duration.normal, easing: easing.bouncy },
  toastExit: { duration: duration.fast, easing: easing.easeIn },

  // Dropdown/popover
  dropdownEnter: { duration: duration.fast, easing: easing.snappy },
  dropdownExit: { duration: duration.faster, easing: easing.easeIn },

  // Page transitions
  pageEnter: { duration: duration.slow, easing: easing.smooth },
  pageExit: { duration: duration.normal, easing: easing.smooth },

  // Skeleton loading
  skeleton: { duration: duration.glacial, easing: easing.easeInOut },
} as const;

// ============================================================================
// CSS Keyframes (as strings for injection)
// ============================================================================

export const keyframes = {
  fadeIn: `
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
  `,
  fadeOut: `
    @keyframes fadeOut {
      from { opacity: 1; }
      to { opacity: 0; }
    }
  `,
  slideInFromTop: `
    @keyframes slideInFromTop {
      from { transform: translateY(-100%); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }
  `,
  slideInFromBottom: `
    @keyframes slideInFromBottom {
      from { transform: translateY(100%); opacity: 0; }
      to { transform: translateY(0); opacity: 1; }
    }
  `,
  slideInFromLeft: `
    @keyframes slideInFromLeft {
      from { transform: translateX(-100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
  `,
  slideInFromRight: `
    @keyframes slideInFromRight {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
  `,
  scaleIn: `
    @keyframes scaleIn {
      from { transform: scale(0.95); opacity: 0; }
      to { transform: scale(1); opacity: 1; }
    }
  `,
  scaleOut: `
    @keyframes scaleOut {
      from { transform: scale(1); opacity: 1; }
      to { transform: scale(0.95); opacity: 0; }
    }
  `,
  spin: `
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
  `,
  pulse: `
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
  `,
  bounce: `
    @keyframes bounce {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-25%); }
    }
  `,
  shimmer: `
    @keyframes shimmer {
      0% { background-position: -200% 0; }
      100% { background-position: 200% 0; }
    }
  `,
} as const;

// ============================================================================
// Portal-specific Motion Preferences
// ============================================================================

export type PortalMotionVariant =
  | "admin"
  | "customer"
  | "reseller"
  | "technician"
  | "management";

export interface PortalMotionConfig {
  enabled: boolean;
  reducedMotion: boolean;
  defaultDuration: keyof typeof duration;
  defaultEasing: keyof typeof easing;
}

export const portalMotion: Record<PortalMotionVariant, PortalMotionConfig> = {
  admin: {
    enabled: true,
    reducedMotion: false,
    defaultDuration: "fast",
    defaultEasing: "smooth",
  },
  customer: {
    enabled: true,
    reducedMotion: false,
    defaultDuration: "normal",
    defaultEasing: "spring",
  },
  reseller: {
    enabled: true,
    reducedMotion: false,
    defaultDuration: "fast",
    defaultEasing: "snappy",
  },
  technician: {
    enabled: false, // Minimal animations for efficiency
    reducedMotion: true,
    defaultDuration: "faster",
    defaultEasing: "linear",
  },
  management: {
    enabled: true,
    reducedMotion: false,
    defaultDuration: "normal",
    defaultEasing: "smooth",
  },
};

// ============================================================================
// Reduced Motion Utilities
// ============================================================================

/**
 * Get animation preset with reduced motion support
 */
export function getAnimation(
  preset: keyof typeof animations,
  prefersReducedMotion = false
): AnimationPreset {
  if (prefersReducedMotion) {
    return { duration: duration.instant, easing: easing.linear };
  }
  return animations[preset];
}

/**
 * Get CSS transition string
 */
export function createTransition(
  properties: string | string[],
  preset: keyof typeof animations = "fadeIn",
  prefersReducedMotion = false
): string {
  const { duration: dur, easing: ease } = getAnimation(preset, prefersReducedMotion);
  const props = Array.isArray(properties) ? properties : [properties];
  return props.map((prop) => `${prop} ${dur} ${ease}`).join(", ");
}
